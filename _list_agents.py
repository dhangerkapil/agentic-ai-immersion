import asyncio, os
from dotenv import load_dotenv
load_dotenv('.env')

async def list_agents():
    from azure.ai.agents.aio import AgentsClient
    from azure.identity import AzureCliCredential
    async with AgentsClient(
        endpoint=os.environ['AI_FOUNDRY_PROJECT_ENDPOINT'],
        credential=AzureCliCredential(),
    ) as client:
        agents = []
        async for a in client.list_agents():
            agents.append(a)
        if not agents:
            print('No agents found in the Foundry project.')
        else:
            print(f'Found {len(agents)} agent(s):')
            print(f'{"Name":<40} {"ID":<40} {"Model"}')
            print('-' * 100)
            for a in agents:
                name = a.name or "(unnamed)"
                print(f'{name:<40} {a.id:<40} {a.model or "N/A"}')

asyncio.run(list_agents())
