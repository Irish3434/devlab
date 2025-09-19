#!/bin/bash

echo "🚀 Picture Finder GitHub Push Script"
echo "===================================="
echo ""

# Check if token is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your GitHub Personal Access Token"
    echo ""
    echo "Usage: ./push_with_token.sh YOUR_TOKEN_HERE"
    echo ""
    echo "Get a token from: https://github.com/settings/tokens"
    echo "Make sure it has 'repo' scope selected!"
    exit 1
fi

TOKEN=$1
REPO_URL="https://$TOKEN@github.com/Irish3434/devlab.git"

echo "🔐 Using token: ${TOKEN:0:8}..."
echo "📤 Pushing to: Irish3434/devlab"
echo ""

# Push to GitHub
if git push "$REPO_URL" main; then
    echo ""
    echo "✅ SUCCESS! Repository pushed to GitHub!"
    echo "🌐 View your repo at: https://github.com/Irish3434/devlab"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "   - Token has 'repo' scope"
    echo "   - Repository exists and you have access"
    echo "   - Token is not expired"
fi