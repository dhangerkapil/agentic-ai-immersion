#!/bin/bash
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Agentic AI Immersion Day                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  User    : $(whoami)"
echo "  Python  : $(python --version 2>&1)"
echo "  Az CLI  : $(az version --query '\"azure-cli\"' -o tsv 2>/dev/null)"
echo ""

if ! az account show > /dev/null 2>&1; then
    echo "  Signing in to Azure — a browser window will open..."
    echo ""
    az login
    echo ""
fi

ACCT_NAME=$(az account show --query "name" -o tsv 2>/dev/null)
ACCT_USER=$(az account show --query "user.name" -o tsv 2>/dev/null)
echo "  Azure subscription : $ACCT_NAME"
echo "  Signed in as       : $ACCT_USER"
echo ""
echo "  Ready. Try: python --version | az account show | jupyter notebook"
echo ""

exec bash -l
