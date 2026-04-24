#!/bin/bash
cd /c/src/agentic-ai-immersion
python -u hosted-agents/src/WebSearchAgent/quick_test.py 2>&1
echo "EXIT_CODE=$?"
