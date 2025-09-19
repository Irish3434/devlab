#!/bin/bash

# Quick GitHub Push Script
# Run this after creating your Personal Access Token

echo "🚀 Picture Finder - Quick GitHub Push"
echo "====================================="

# Check if token is provided as argument
if [ "$1" ]; then
    TOKEN="$1"
    echo "✅ Using provided token"
else
    echo "💡 Usage: ./quick_push.sh YOUR_PERSONAL_ACCESS_TOKEN"
    echo ""
    echo "Or create token at: https://github.com/settings/tokens"
    echo "Required scopes: repo, workflow, write:packages"
    exit 1
fi

echo "🔧 Configuring Git..."
git remote set-url origin "https://Irish3434:${TOKEN}@github.com/Irish3434/devlab.git"
git config --local user.name "Irish3434"
git config --local user.email "irish3434@users.noreply.github.com"

echo "🚀 Pushing to GitHub..."
if git push -u origin main; then
    echo ""
    echo "🎉 SUCCESS! Picture Finder pushed to GitHub!"
    echo "🌟 Repository: https://github.com/Irish3434/devlab"
    echo "📊 View your enhanced Picture Finder online!"
    
    # Clean up credentials
    git remote set-url origin "https://github.com/Irish3434/devlab.git"
    echo "🔒 Credentials cleaned from git config"
else
    echo "❌ Push failed. Please check your token permissions."
fi