#!/bin/bash

# Picture Finder - Simple GitHub Authentication Helper
# This script guides you through GitHub authentication

echo "🔑 GitHub Authentication Helper"
echo "==============================="
echo
echo "Your Picture Finder application is ready to upload!"
echo
echo "🎯 Quick Setup (30 seconds):"
echo
echo "1. Open this link: https://github.com/settings/tokens/new"
echo "2. Set Token name: 'Picture Finder Upload'"
echo "3. Select scope: ☑️ repo (Full control of private repositories)"
echo "4. Click 'Generate token'"
echo "5. Copy the token (starts with ghp_...)"
echo
echo "Then run:"
echo "  git push -u origin main"
echo
echo "When prompted:"
echo "  Username: Irish3434"
echo "  Password: [paste your token here]"
echo
echo "🔗 Direct link: https://github.com/settings/tokens/new?scopes=repo&description=Picture%20Finder%20Upload"
echo
echo "✨ After upload, your app will be available at:"
echo "   https://github.com/Irish3434/devlab"

# Try to open the URL automatically
if command -v open >/dev/null 2>&1; then
    echo
    read -p "🌐 Open GitHub token page automatically? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "https://github.com/settings/tokens/new?scopes=repo&description=Picture%20Finder%20Upload"
        echo "✅ GitHub opened in your browser!"
    fi
fi