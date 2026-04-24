#!/bin/bash
echo "SCRIPT_START"
python -u hosted-agents/src/WebSearchAgent/quick_test.py 2>&1
RC=$?
echo "SCRIPT_EXIT_CODE=$RC"
echo "SCRIPT_END"
