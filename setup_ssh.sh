#!/bin/bash

# SSH Setup for GitHub - Alternative to Personal Access Token
echo "🔐 Setting up SSH authentication for GitHub..."

# Check if SSH key exists
if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ SSH key found!"
    echo ""
    echo "📋 ADD THIS SSH KEY TO GITHUB:"
    echo "================================="
    cat ~/.ssh/id_ed25519.pub
    echo "================================="
    echo ""
    echo "🔗 Go to: https://github.com/settings/keys"
    echo "1. Click 'New SSH key'"
    echo "2. Title: 'Picture Finder Development'"
    echo "3. Paste the key above"
    echo "4. Click 'Add SSH key'"
    echo ""
    
    # Set up SSH remote
    echo "🔧 Configuring SSH remote..."
    git remote set-url origin git@github.com:Irish3434/devlab.git
    
    echo "✅ SSH configured!"
    echo "🚀 Now run: git push -u origin main"
else
    echo "❌ No SSH key found. Use Personal Access Token method instead."
fi