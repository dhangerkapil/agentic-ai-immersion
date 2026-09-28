"""Lab 2, notebook part: Foundry IQ knowledge base over Azure AI Search.

Runs on:  the learner workstation (notebook or python). Nothing here ships in the container.
Goal:     Turn data/knowledge/*.md into two search indexes (marketplace and accounts, each with
          the universal docs), two knowledge sources, one knowledge base (via-benefits-kb) and a
          project connection so a managed identity can call the knowledge base over MCP. The hosted
          agent in hosted/main.py reaches the same MCP endpoint with MCPStreamableHTTPTool.
Inputs:   artifacts/lab1/hosted.json (chain check: Lab 1 deployed the basics agent); data/knowledge
Outputs:  artifacts/lab2/knowledge.json  indexes, knowledge sources, kb name, mcp endpoint, connection
Time:     about 15 min of the Do block (the index build itself takes 1 to 2 min)

Run:      python knowledge_base.py                   build + demo (direct index queries)
          python knowledge_base.py --skip-connection  build indexes and kb only (no ARM call)
          python knowledge_base.py --demo-only
lab2_hosted_knowledge.py imports this module and calls build() as its first step.
"""
# %% Imports and environment
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # wtw-foundry-hosted-agents-labs/ (common/ and data/ live here)
sys.path.insert(0, str(ROOT))
from common import via_data, foundry_env, guardrails  # noqa: E402,F401

LABS_DIR = Path(__file__).resolve().parents[1]  # labs/ (lab_helpers.py, catch_up.py, artifacts/)
sys.path.insert(0, str(LABS_DIR))
import lab_helpers as helpers  # noqa: E402

import requests  # noqa: E402
from azure.identity import AzureCliCredential, get_bearer_token_provider  # noqa: E402
from azure.search.documents import SearchClient  # noqa: E402
from azure.search.documents.indexes import SearchIndexClient  # noqa: E402
from azure.search.documents.indexes.models import (  # noqa: E402
    AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters, HnswAlgorithmConfiguration, KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel, KnowledgeSourceReference, SearchField, SearchFieldDataType, SearchIndex,
    SearchIndexFieldReference, SearchIndexKnowledgeSource, SearchIndexKnowledgeSourceParameters,
    SemanticConfiguration, SemanticField, SemanticPrioritizedFields, SemanticSearch, VectorSearch,
    VectorSearchProfile)
from openai import AzureOpenAI  # noqa: E402

ENV = foundry_env.load_env()
MODEL = helpers.pick_model(ENV)
EMBEDDING = ENV.get("EMBEDDING_MODEL_DEPLOYMENT_NAME") or "text-embedding-3-large"
LAB = "lab2"

# %% Names: one bounded context per index, universal docs in both
INDEXES = {
    "via-kb-marketplace": ["marketplace", "universal"],
    "via-kb-accounts": ["accounts", "universal"],
}
KNOWLEDGE_SOURCES = {"marketplace-ks": "via-kb-marketplace", "accounts-ks": "via-kb-accounts"}
KB_NAME = "via-benefits-kb"
CONNECTION_NAME = "via-benefits-kb-connection"
KB_API_VERSION = "2025-11-01-Preview"
ARM_API_VERSION = "2025-10-01-preview"
VECTOR_DIMS = 3072                      # text-embedding-3-large
VECTOR_PROFILE = "via-vector-profile"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def search_endpoint() -> str:
    endpoint = ENV.get("AZURE_AI_SEARCH_ENDPOINT")
    if not endpoint:
        raise SystemExit("[lab2] AZURE_AI_SEARCH_ENDPOINT is not set in .env (see SETUP.md)")
    return endpoint.rstrip("/")


def aoai_resource_url() -> str:
    """Resource URL for the vectorizer and the knowledge base model (no /openai/ suffix)."""
    endpoint = ENV.get("AZURE_OPENAI_ENDPOINT")
    if endpoint:
        return endpoint.split("/openai/")[0].rstrip("/")
    project = ENV.get("FOUNDRY_PROJECT_ENDPOINT", "")
    host = re.match(r"https://[^/]+", project)
    if not host:
        raise SystemExit("[lab2] set AZURE_OPENAI_ENDPOINT (or FOUNDRY_PROJECT_ENDPOINT) in .env")
    print(f"[lab2] AZURE_OPENAI_ENDPOINT not set, using the Foundry host {host.group(0)}")
    return host.group(0)


# %% Documents: frontmatter, heading chunks, index records
def split_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.split("#")[0].strip().strip('"')
    return meta, text[match.end():]


def chunk_by_heading(body: str, min_words: int = 40) -> list[tuple[str, str]]:
    """Split Markdown on headings; fold very short sections into the previous one."""
    chunks: list[tuple[str, list[str]]] = []
    heading = "Introduction"
    for line in body.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip() or heading
            chunks.append((heading, []))
            continue
        if not chunks:
            chunks.append((heading, []))
        chunks[-1][1].append(line)
    merged: list[tuple[str, str]] = []
    for title, lines in chunks:
        text = "\n".join(lines).strip()
        if not text:
            continue
        if merged and len(text.split()) < min_words:
            prev_title, prev_text = merged[-1]
            merged[-1] = (prev_title, f"{prev_text}\n\n{title}\n{text}")
        else:
            merged.append((title, text))
    return merged


def load_records(contexts: list[str]) -> list[dict]:
    """One index record per heading chunk, tagged with doc_id and context for citations and filters."""
    records = []
    for context in contexts:
        for doc in via_data.list_knowledge_docs(context):
            meta, body = split_frontmatter(via_data.read_knowledge_doc(doc["doc_id"]))
            title = meta.get("title") or doc["title"]
            for n, (heading, text) in enumerate(chunk_by_heading(body), start=1):
                records.append({
                    "id": f"{doc['doc_id']}-{n}",
                    "title": f"{title}: {heading}",
                    "content": f"[{doc['doc_id']}] {title}\n{heading}\n\n{text}",
                    "doc_id": doc["doc_id"],
                    "context": doc.get("context", context),
                })
    return records


# %% Embeddings (Entra token, no keys)
def make_embedder(credential):
    client = AzureOpenAI(
        azure_endpoint=aoai_resource_url(),
        azure_ad_token_provider=get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default"),
        api_version="2024-02-01",
    )

    def embed(texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 16):
            batch = texts[start:start + 16]
            result = client.embeddings.create(input=batch, model=EMBEDDING)
            vectors.extend(item.embedding for item in result.data)
        return vectors

    return embed


# %% Index definition: keyword + vector + semantic, vectorizer for query-time embeddings
def index_definition(name: str) -> SearchIndex:
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchField(name="title", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="doc_id", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="context", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=VECTOR_DIMS,
                    vector_search_profile_name=VECTOR_PROFILE),
    ]
    # VERIFY against https://learn.microsoft.com/python/api/azure-search-documents/ before delivery:
    # keyword names vectorizer_name / algorithm_configuration_name on 11.7.0b2.
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="via-hnsw")],
        profiles=[VectorSearchProfile(name=VECTOR_PROFILE, algorithm_configuration_name="via-hnsw",
                                      vectorizer_name="via-aoai-vectorizer")],
        vectorizers=[AzureOpenAIVectorizer(
            vectorizer_name="via-aoai-vectorizer",
            parameters=AzureOpenAIVectorizerParameters(resource_url=aoai_resource_url(),
                                                       deployment_name=EMBEDDING, model_name=EMBEDDING))],
    )
    semantic = SemanticSearch(
        default_configuration_name="via-semantic",
        configurations=[SemanticConfiguration(
            name="via-semantic",
            prioritized_fields=SemanticPrioritizedFields(title_field=SemanticField(field_name="title"),
                                                         content_fields=[SemanticField(field_name="content")]))],
    )
    return SearchIndex(name=name, fields=fields, vector_search=vector_search, semantic_search=semantic)


def build_index(index_client: SearchIndexClient, credential, name: str, contexts: list[str], embed) -> int:
    index_client.create_or_update_index(index_definition(name))
    records = load_records(contexts)
    for record, vector in zip(records, embed([r["content"] for r in records])):
        record["content_vector"] = vector
    SearchClient(endpoint=search_endpoint(), index_name=name, credential=credential).upload_documents(records)
    doc_ids = sorted({r["doc_id"] for r in records})
    print(f"[lab2] index {name}: {len(records)} chunks from {len(doc_ids)} docs {doc_ids}")
    return len(records)


# %% Knowledge sources and the knowledge base
def build_knowledge_sources(index_client: SearchIndexClient) -> None:
    for ks_name, index_name in KNOWLEDGE_SOURCES.items():
        source = SearchIndexKnowledgeSource(
            name=ks_name,
            description=f"Via Benefits functional documentation, {index_name.split('-')[-1]} context",
            search_index_parameters=SearchIndexKnowledgeSourceParameters(
                search_index_name=index_name,
                source_data_fields=[SearchIndexFieldReference(name="content"), SearchIndexFieldReference(name="title")]),
        )
        # VERIFY against the azure-search-documents 11.7.0b2 reference before delivery (method name).
        index_client.create_or_update_knowledge_source(knowledge_source=source)
        print(f"[lab2] knowledge source {ks_name} -> {index_name}")


def build_knowledge_base(index_client: SearchIndexClient) -> KnowledgeBase:
    kb = KnowledgeBase(
        name=KB_NAME,
        description="Via Benefits Individual Marketplace knowledge: plans, enrollment periods, HRA rules, "
                    "handoff and privacy policy. Retrieve first, then cite doc ids like [KB-ACC-001].",
        knowledge_sources=[KnowledgeSourceReference(name=ks) for ks in KNOWLEDGE_SOURCES],
        models=[KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
            resource_url=aoai_resource_url(), deployment_name=MODEL, model_name=MODEL))],
    )
    index_client.create_or_update_knowledge_base(knowledge_base=kb)
    print(f"[lab2] knowledge base {KB_NAME} with sources {list(KNOWLEDGE_SOURCES)}")
    return kb


def mcp_endpoint() -> str:
    return f"{search_endpoint()}/knowledgebases/{KB_NAME}/mcp?api-version={KB_API_VERSION}"


# %% Project connection (ARM) so the project managed identity can call the MCP endpoint
def create_project_connection(credential, target: str) -> dict:
    project_resource_id = ENV.get("PROJECT_RESOURCE_ID")
    if not project_resource_id:
        raise SystemExit("[lab2] PROJECT_RESOURCE_ID is not set in .env; needed for the project connection")
    url = f"https://management.azure.com{project_resource_id}/connections/{CONNECTION_NAME}?api-version={ARM_API_VERSION}"
    token = credential.get_token("https://management.azure.com/.default").token
    body = {
        "name": CONNECTION_NAME,
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": target,
            "isSharedToAll": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"},
        },
    }
    response = requests.put(url, json=body, timeout=60,
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    if response.status_code not in (200, 201):
        raise SystemExit(f"[lab2] connection PUT failed {response.status_code}: {response.text[:500]}")
    connection_id = response.json().get("id") or f"{project_resource_id}/connections/{CONNECTION_NAME}"
    print(f"[lab2] project connection {CONNECTION_NAME} -> {target}")
    return {"connection_name": CONNECTION_NAME, "connection_id": connection_id, "target": target}


# %% build(): everything above, then the checkpoint artifact
def build(skip_connection: bool = False) -> dict:
    lab1 = helpers.require_artifact("lab1", "hosted.json", through=1, caller="lab2")
    credential = AzureCliCredential()
    index_client = SearchIndexClient(endpoint=search_endpoint(), credential=credential)
    embed = make_embedder(credential)
    counts = {name: build_index(index_client, credential, name, contexts, embed) for name, contexts in INDEXES.items()}
    build_knowledge_sources(index_client)
    build_knowledge_base(index_client)
    info = {
        "lab": LAB,
        "built_after": {"agent_name": lab1.get("agent_name"), "agent_version": lab1.get("agent_version")},
        "search_endpoint": search_endpoint(),
        "indexes": counts,
        "knowledge_sources": KNOWLEDGE_SOURCES,
        "kb_name": KB_NAME,
        "mcp_endpoint": mcp_endpoint(),
        "retrieval_tool_name": "knowledge_base_retrieve",
        "connection": {} if skip_connection else create_project_connection(credential, mcp_endpoint()),
        "created_at": helpers.now_iso(),
    }
    path = helpers.artifact_path(LAB, "knowledge.json")
    if path.exists():
        info = {**foundry_env.load_artifact(path), **info}      # keep hosted info written by lab2_hosted_knowledge
    foundry_env.save_artifact(path, info)
    print(f"[lab2] saved {path.relative_to(LABS_DIR)}")
    if skip_connection:
        print("[lab2] connection skipped: rerun without --skip-connection before building the agent")
    return info


# %% demo(): query the indexes directly, the same way the knowledge base will
def demo(questions: dict[str, str] | None = None) -> None:
    helpers.require_artifact(LAB, "knowledge.json", through=2, caller="lab2")
    credential = AzureCliCredential()
    questions = questions or {
        "via-kb-marketplace": "When is the annual enrollment period and what can I change?",
        "via-kb-accounts": "Which documents count as proof of payment for a premium claim?",
    }
    for index_name, question in questions.items():
        client = SearchClient(endpoint=search_endpoint(), index_name=index_name, credential=credential)
        hits = client.search(search_text=question, top=3, select=["doc_id", "title", "context"])
        print(f"[lab2] {index_name}: {question}")
        for hit in hits:
            print(f"[lab2]   {hit['doc_id']:<11} {hit['title'][:70]}  ({hit['context']})")
    print(f"[lab2] knowledge base MCP endpoint: {mcp_endpoint()}")
    print("[lab2] portal: Azure AI Search > Knowledge bases > via-benefits-kb; Foundry > Management center > Connections")
    print("[lab2] the hosted agent reads this endpoint from VIA_KB_MCP_URL (lab2_hosted_knowledge.py sets it)")


# %% YOUR TURN (5 min): semantic ranking
# Rerun one query with semantic ranking and captions. Compare the order of hits.
#
# Solution:
#   client = SearchClient(endpoint=search_endpoint(), index_name="via-kb-accounts", credential=AzureCliCredential())
#   for hit in client.search(search_text="my card was declined at the pharmacy", top=3,
#                            query_type="semantic", semantic_configuration_name="via-semantic",
#                            query_caption="extractive", select=["doc_id", "title"]):
#       print(hit["doc_id"], hit["title"], (hit.get("@search.captions") or [None])[0])

# %% YOUR TURN (5 min): scope retrieval by context
# The universal docs live in both indexes. Filter them out of a marketplace query with an OData filter.
#
# Solution:
#   client = SearchClient(endpoint=search_endpoint(), index_name="via-kb-marketplace", credential=AzureCliCredential())
#   for hit in client.search(search_text="when may an assistant recommend a plan", top=3,
#                            filter="context eq 'marketplace'", select=["doc_id", "title"]):
#       print(hit["doc_id"], hit["title"])
#   # Now the licensing rules in KB-UNI-001 are gone. Teaching point: that document belongs in every context.

# %% YOUR TURN (5 min): change the chunking
# Set min_words=120 in chunk_by_heading and rebuild via-kb-accounts. Count the chunks before and after,
# then rerun the proof-of-payment query. Bigger chunks carry more context but blur citations.
#
# Solution:
#   credential = AzureCliCredential()
#   index_client = SearchIndexClient(endpoint=search_endpoint(), credential=credential)
#   original = chunk_by_heading.__defaults__
#   chunk_by_heading.__defaults__ = (120,)
#   build_index(index_client, credential, "via-kb-accounts", INDEXES["via-kb-accounts"], make_embedder(credential))
#   chunk_by_heading.__defaults__ = original


# %% Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-connection", action="store_true", help="skip the ARM connection PUT")
    parser.add_argument("--demo-only", action="store_true", help="query existing indexes only")
    args = parser.parse_args()
    if not args.demo_only:
        build(skip_connection=args.skip_connection)
    demo()
