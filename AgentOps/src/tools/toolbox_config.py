"""Create/update a versioned Foundry Toolbox for the Benefits Concierge (toolbox-as-code).

The toolbox definition lives in source control and is deployed through CI
(.github/workflows/build-deploy.yml). Because the toolbox endpoint is stable, the
agent picks up tool changes without redeployment.

Requires the preview Toolboxes feature (azure-ai-projects >= 2.2.0, allow_preview=True).
Run via CI or locally:  python src/tools/toolbox_config.py

Learn more: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox
"""
import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import CodeInterpreterTool, WebSearchTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

TOOLBOX_NAME = os.environ.get("TOOLBOX_NAME", "benefits-concierge-tools")


def main() -> None:
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]
    with AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True) as client:
        # Each tool needs a unique 'name' identifier when more than one is present.
        version = client.beta.toolboxes.create_version(
            TOOLBOX_NAME,
            description="Tools for the employee benefits concierge: web search + code interpreter.",
            tools=[
                WebSearchTool(name="web_search"),
                CodeInterpreterTool(name="code_interpreter"),
            ],
        )
        print(f"Created toolbox '{TOOLBOX_NAME}' version: {version.version}")
        client.beta.toolboxes.update(TOOLBOX_NAME, default_version=version.version)
        print(f"Default version of '{TOOLBOX_NAME}' is now: {version.version}")


if __name__ == "__main__":
    main()
