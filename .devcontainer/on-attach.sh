#!/bin/bash
# Runs as postAttachCommand — output appears in VS Code's startup log.
touch /tmp/.vscode-attached

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Agentic AI Immersion Day — Environment Ready        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Python  : $(python --version 2>&1)"
echo "  Az CLI  : $(az version --query '\"azure-cli\"' -o tsv 2>/dev/null)"
echo "  azd     : $(azd version 2>/dev/null | head -1)"
echo ""
echo "  Opening workshop terminal..."
echo ""
