# Lab 1: Hosted agent basics

| | |
|---|---|
| Goal | Build the Via Benefits concierge as a Microsoft Foundry Hosted Agent, run it locally on port 8088, chat S1 and S2 through `POST /responses`, then deploy the same folder from source with `azd` and invoke the version Foundry runs. |
| Time | 60 min: teach 10, demo 10, do 35, checkpoint 5 |
| Starts from | nothing (this is the first lab); `.env` with `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `PROJECT_RESOURCE_ID` |
| Produces | `artifacts/lab1/hosted.json`, `artifacts/lab1/transcripts.md`, `artifacts/lab1/hosted_local.log` |
| Learn path modules | 7 Develop an AI agent with Microsoft Agent Framework; 2 Integrate custom tools into your agent; 1 Develop AI agents with Microsoft Foundry and Visual Studio Code |

**Where this runs:** both. `lab1_walkthrough.ipynb` / `lab1_hosted_basics.py` run on your workstation (the cockpit); `hosted/main.py` runs as a local process for testing and then as a container Foundry builds and runs for you (the product).

## What you'll learn
- Build an Agent Framework `Agent` on `FoundryChatClient` with three `@tool` functions over the systems of record and the shared compliance block.
- Serve that agent over the OpenAI Responses protocol with `ResponsesHostServer`, and explain what Foundry does with the folder when you run `azd up`.
- Call a hosted agent the way a web chat backend does: `POST /responses` locally, `responses.create(..., agent_reference)` for the deployed version.
- Explain the RBAC split (Foundry Project Manager to deploy, Foundry Agent Consumer or Foundry User to invoke) and read a version's status and logs in the portal.
- Ship a second version by changing one instruction and re-running `azd up`, and say why the old version stays.
- Diagnose the two startup failures learners hit most: a failed version (bad ZIP or pins) and `424 session_not_ready`.

## Technical features taught

| Feature | Foundry / SDK object | Where in the code | Why it matters for Via Benefits |
|---|---|---|---|
| Foundry chat client with Entra identity | `agent_framework.foundry.FoundryChatClient(project_endpoint, model, credential=DefaultAzureCredential())` | `hosted/main.py` `build_agent()` | `az login` locally, the hosted agent's managed identity in Foundry; no keys in code or env |
| Agent with typed tools | `agent_framework.Agent`, `@tool(approval_mode="never_require")`, `Annotated[str, Field(...)]` | `hosted/main.py` tools cell, `TOOLS` | The model reads participant, window and HRA facts from `via_data` instead of guessing |
| Shared compliance block | `guardrails.COMPLIANCE_INSTRUCTIONS` appended to `ROLE_INSTRUCTIONS` (asserted) | `hosted/main.py` instructions cell | Licensing and PHI rules travel with every agent in every lab |
| Responses protocol host | `agent_framework_foundry_hosting.ResponsesHostServer(agent).run()` | `hosted/main.py` `__main__` | One code path for local testing (port 8088) and the Foundry container |
| Stateless model calls | `default_options={"store": False}` | `hosted/main.py` `build_agent()` | The model service keeps no transcript; Lab 2 puts history where you control it |
| Flat deployable folder | `hosted/prepare.py` vendors `common/` and `data/`; `requirements.txt` with explicit pins | `lab1_hosted_basics.py` `build()` | The ZIP azd uploads must be flat and self-contained; `agent-framework[foundry]` breaks the remote build |
| Local process management | `subprocess.Popen` + port probe | `lab1_hosted_basics.py` `HostedProcess` | Same lifecycle Foundry manages: start, readiness, logs, stop |
| Calling the protocol | `httpx.post(f"{base}/responses", json={"input": ..., "previous_response_id": ...})` | `lab1_hosted_basics.py` `post_responses()` | This is what WTW's web chat backend sends; `previous_response_id` carries the turn chain |
| Deploy from source | `azd ai agent init --protocol responses --deploy-mode code --runtime python_3_14 --dep-resolution remote_build`, `azd up` | `lab1_hosted_basics.py` `deploy_commands()` | No Docker or ACR on the laptop; Foundry builds, versions and scales |
| Invoke the deployed version | `openai_client.responses.create(input, extra_body={"agent_reference": {...}})` | `lab1_hosted_basics.py` `call_deployed()`, `hosted/test_local.py --deployed` | Same call shape as any Foundry agent; the smoke test Lab 4 automates |

## Teach (10 min)
- A hosted agent is your code, run by Foundry. You hand it a flat folder (`main.py`, `requirements.txt`, whatever it imports). `azd up` zips it, uploads it, Foundry restores the pinned packages in a remote build, provisions an isolated runtime, creates an agent identity, exposes the protocol endpoint you declared, and records a **version**. Foundry runs and scales the container; you never see a Dockerfile.
- Two protocols, one build pattern. `FoundryChatClient -> Agent -> host server`. `ResponsesHostServer` speaks the OpenAI Responses protocol (multi-turn, streaming, model-directed tools). `InvocationsHostServer` speaks a single structured request/response (Stretch 6). Only the last line differs.
- Identity: locally `DefaultAzureCredential` resolves to your `az login`; in the container it resolves to the agent's managed identity. That identity needs to reach the model deployment in the project. No connection strings, no API keys.
- RBAC: whoever runs `azd up` needs **Foundry Project Manager** at project scope. Whoever calls the endpoint needs **Foundry Agent Consumer** (invoke only) or **Foundry User** (develop and invoke). Role propagation takes minutes; 403 on deploy is almost always the first, 403 on invoke the second.
- Versions are immutable. A change to the ZIP hash or the definition creates a new version. Failed versions stay visible for audit. Wait for status `active` before invoking; do not test a version that is still `creating`.
- Tools are plain Python functions with typed parameters. The framework builds the JSON schema from the `Annotated[..., Field(description=...)]` hints and runs the tool loop. Our tools read synthetic systems of record in `data/`; in production they call WTW's APIs.
- The compliance block is not a suggestion. Every agent in this sequence appends `guardrails.COMPLIANCE_INSTRUCTIONS`, and `test_local.py` fails when an answer recommends a plan or leaks PII. That is the operating model: agents summarise, retrieve and hand off; licensed advisors decide.

```
workstation (cockpit)                          Microsoft Foundry (product)
+----------------------------------+           +--------------------------------------------+
| lab1_walkthrough.ipynb           |  azd up   | project                                     |
|  build(): prepare.py vendors     | --------> |  hosted agent via-concierge-hosted          |
|  demo():  POST /responses -----> |           |    version 1  status: active                |
|           to hosted/main.py      |           |    +------------------------------------+   |
|           on localhost:8088      |           |    | container built from the ZIP       |   |
|  call_deployed(): responses      |           |    |  main.py: Agent + FoundryChatClient|   |
|           .create(agent_ref) --> | --------> |    |  ResponsesHostServer  /responses   |   |
+----------------------------------+           |    |  identity: managed identity ------>|-> model deployment
                                               |    +------------------------------------+   |
                                               +--------------------------------------------+
```

## Demo (10 min)
1. `cd labs && python lab1-hosted-agent-basics/lab1_hosted_basics.py`. Point at the log lines: `vendored common/`, `wrote artifacts/lab1/hosted.json`, `started hosted/main.py (pid ...) on port 8088`, `server is accepting connections`. Say: "Foundry does the last two lines for you in the cloud."
2. Read S1 turn 1 aloud: identity by participant id and ZIP only, then the enrollment window (AEP) from `get_enrollment_window`. Then S1 turn 2, "Just tell me which plan I should pick": the agent declines and offers a licensed advisor. Point at `checks: no_recommendation=OK, no_pii=OK`.
3. Open `artifacts/lab1/hosted_local.log`: the `[hosted] agent via-concierge-hosted: model=... tools=[...]` line is what you will read in the portal's version logs later.
4. `python lab1-hosted-agent-basics/lab1_hosted_basics.py --deploy`. Walk the azd lines: `init` declares protocol, runtime, entry point and remote build; `up` packages and waits. Run them if the room's project is ready (3-6 minutes). In the portal: Agents -> `via-concierge-hosted` -> Versions -> status, then Logs. Show the same `[hosted] agent ...` line.
5. `python lab1-hosted-agent-basics/hosted/test_local.py --deployed`: same three questions, same checks, against the version Foundry runs.

## Do (35 min)
1. **Run it locally (5 min).** `cd labs && python lab1-hosted-agent-basics/lab1_hosted_basics.py`. You should see both scenarios and `wrote artifacts/lab1/transcripts.md`. Open the transcript. Checkpoint: S1 turn 2 offers an advisor and does not name a plan.
2. **Keep a server running (5 min).** Terminal 1: `cd labs/lab1-hosted-agent-basics/hosted && python main.py`. Terminal 2: `python test_local.py`. Then in the notebook: `post_responses("http://localhost:8088", "Hi, this is P-1005, ZIP 84010. What is my enrollment window?")["text"]`. You should see the ACA open enrollment window for a pre-Medicare participant.
3. **YOUR TURN (5 min): add `get_sponsor`.** In `hosted/main.py`, wrap `via_data.get_sponsor(sponsor_id)` with `@tool` like the other three and append it to `TOOLS` (solution in the commented block). Restart `main.py`. Ask as P-1001: "Who is my plan sponsor and how much is the HRA for the year?" You should see the sponsor name and the annual amount from the tool result, not invented.
4. **Deploy (10 min).** `python lab1-hosted-agent-basics/lab1_hosted_basics.py --deploy`, then run the printed commands from `hosted/`. Watch `azd up` finish with a version. In the portal wait for `active`. Record it: `python lab1_hosted_basics.py --record-version <n>`. Run `python hosted/test_local.py --deployed`. You should see `PASS`.
5. **YOUR TURN (10 min): tighten an instruction and ship a new version.** Change rule 3 in `ROLE_INSTRUCTIONS` so the agent always names the enrollment window when it offers an advisor. Test locally (S1 turn 2 should now mention AEP). `azd up` again. In the portal you now have two versions; the old one is still there. Record the new version. Say in one sentence why immutable versions matter for a regulated call center.
6. **YOUR TURN (5 min): call the deployed endpoint from the notebook.** `call_deployed("Hi, this is P-1003, ZIP 84604. Why was CLM-9003 denied?")["text"]`. Then run `lab1_hosted_basics.py --deployed` to regenerate `transcripts.md` from the cloud version. Compare with the local transcript.

## Checkpoint (5 min)
Paste in the room chat: the S1 turn 2 answer (the refusal plus the advisor offer) and the `deployed` block of `artifacts/lab1/hosted.json`. Lab 2 needs `artifacts/lab1/hosted.json` to exist; the deployed version may still be `null` if your `azd up` is queued, Lab 2 redeploys anyway.

## If you're behind
`cd labs && python catch_up.py --through 1` vendors the folder and writes `hosted.json` without calling Azure. Skip the deploy step and do it during Lab 2's build, which redeploys the same agent name as a new version.

## Stretch (only if you're done early)
Add `stream=True` to the request body in `post_responses` and iterate the server-sent events instead of waiting for the full response; print tokens as they arrive.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT is not set` when `main.py` starts | `.env` not at the repo root or not loaded | Copy `.env.example` to `.env` at the base repo root; the driver loads it and passes it to the child process |
| `ModuleNotFoundError: common` inside `hosted/` | `prepare.py` not run | `python prepare.py` in `hosted/` (build() does this); re-run after editing `common/` or `data/` |
| 401 on deploy or invoke | Wrong tenant or subscription in `az account show` | `az login`, `az account set --subscription <id>`; the token audience is `https://ai.azure.com` |
| 403 on `azd up` | Deployer lacks Foundry Project Manager at project scope | Assign the role; wait 5-15 min for propagation; Foundry User alone cannot create hosted versions |
| 403 on invoke | Caller lacks Foundry Agent Consumer or Foundry User | Assign at project scope, wait for propagation |
| Version status `failed`, CodeError | ZIP has a wrapper folder, or `requirements.txt` uses `agent-framework[foundry]` | Keep the folder flat, keep explicit package pins, redeploy; read the version's `error.message` |
| `424 session_not_ready` on invoke | Container is still starting or crashed at startup | Capture the `x-agent-session-id` header, stream `.../sessions/{id}:logstream?api-version=v1`, fix startup (usually an import or missing env), deploy a new version |
| HTTP 500 from the deployed agent on the first turn | The agent's managed identity cannot reach the model deployment | Check the hosted agent's identity has the project role Foundry assigns on deploy; wait for propagation; retry |
| `model not found` in the logs | `AZURE_AI_MODEL_DEPLOYMENT_NAME` does not match a deployment in the project | Deploy `gpt-5.4-mini` (or set the env var to an existing deployment) in a supported region |
| Port 8088 already in use locally | Another `main.py` still running | Stop it, or set `VIA_HOSTED_PORT=8089` for both `main.py` and the driver |

## References
- Learn: [Develop an AI agent with Microsoft Agent Framework](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (module 7), [Integrate custom tools into your agent](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (module 2)
- Hosted agents concepts and deploy from source: https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents
- Base repo reused: `hosted-agents/benefits-advisor-responses/main.py` (build pattern), `hosted-agents/README.md` (azd commands, RBAC, troubleshooting table)
