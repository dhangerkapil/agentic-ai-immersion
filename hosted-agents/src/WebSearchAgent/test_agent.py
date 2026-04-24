"""
Test script for WebSearchAgent - tests imports, configuration, and a live web search query.
"""

import os
import sys
import asyncio
from pathlib import Path

# Load environment variables from root .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')


def test_imports():
    """Test that all required modules can be imported."""
    print("=" * 60)
    print("TEST 1: Imports")
    print("=" * 60)
    try:
        from agent_framework import Agent, Message
        from agent_framework_azure_ai import AzureAIAgentClient
        from azure.ai.agentserver.agentframework import from_agent_framework
        from azure.identity.aio import DefaultAzureCredential
        print("[PASS] All imports successful")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_env_vars():
    """Test that all required environment variables are set."""
    print("\n" + "=" * 60)
    print("TEST 2: Environment Variables")
    print("=" * 60)
    required_vars = [
        "AI_FOUNDRY_PROJECT_ENDPOINT",
        "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        "BING_CONNECTION_ID",
    ]
    all_set = True
    for var in required_vars:
        if var in os.environ:
            # Mask the value for security
            val = os.environ[var]
            masked = val[:8] + "..." if len(val) > 8 else "***"
            print(f"  [PASS] {var} = {masked}")
        else:
            print(f"  [FAIL] {var} is NOT set")
            all_set = False
    return all_set


def main():
    print("WebSearchAgent Test Suite")
    print("=" * 60)

    # Test 1: Imports
    if not test_imports():
        print("\n[ABORT] Cannot proceed without required imports.")
        sys.exit(1)

    # Test 2: Environment Variables
    if not test_env_vars():
        print("\n[ABORT] Cannot proceed without required environment variables.")
        sys.exit(1)

    # Test 3: Agent Creation
    from agent_framework import Agent, Message
    from agent_framework_azure_ai import AzureAIAgentClient
    from azure.identity.aio import DefaultAzureCredential

    print("\n" + "=" * 60)
    print("TEST 3: Agent Creation")
    print("=" * 60)

    try:
        chat_client = AzureAIAgentClient(
            endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
            async_credential=DefaultAzureCredential(),
        )

        bing_search_tool = AzureAIAgentClient.get_web_search_tool(
            bing_connection_id=os.environ["BING_CONNECTION_ID"],
        )

        agent = Agent(
            client=chat_client,
            name="WebSearchAgent",
            instructions=(
                "You are a helpful assistant that can search the web for current information. "
                "Use the Bing search tool to find up-to-date information and provide accurate, "
                "well-sourced answers. Always cite your sources when possible. "
                "For time-sensitive queries, include the date of the information when available."
            ),
            tools=[bing_search_tool],
        )
        print(f"  [PASS] Agent created: name='{agent.name}'")
    except Exception as e:
        print(f"  [FAIL] Agent creation failed: {type(e).__name__}: {e}")
        sys.exit(1)

    # Test 4: Live Query
    print("\n" + "=" * 60)
    print("TEST 4: Live Web Search Query")
    print("=" * 60)
    print("  Sending query: 'What is the current weather in Seattle?'")
    print("  (Calling Azure AI + Bing Grounding...)\n")

    async def run_query():
        try:
            messages = [Message("user", ["What is the current weather in Seattle?"])]
            response = await agent.run(messages)

            full_response = response.message.text if response.message else ""
            if full_response:
                print(f"  [PASS] Got response ({len(full_response)} chars):")
                preview = full_response[:500]
                for line in preview.split('\n'):
                    print(f"    {line}")
                if len(full_response) > 500:
                    print(f"    ... (truncated)")
            else:
                print("  [WARN] Empty response received")
            return True
        except Exception as e:
            print(f"  [FAIL] Live query failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    success = asyncio.run(run_query())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    if success:
        print("[ALL PASS] WebSearchAgent is working correctly!")
    else:
        print("[PARTIAL] Agent creation works but live query had issues.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
