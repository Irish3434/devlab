#!/bin/bash

# PictureFinder - Automatic GitHub Setup Script
# This script sets up and pushes your repository to GitHub

echo "🚀 Picture Finder - Automatic GitHub Setup"
echo "=========================================="
echo

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the PictureFinder directory"
    exit 1
fi

echo "📂 Current directory: $(pwd)"
echo "📋 Repository status:"
git status --short

echo
echo "🔧 Setting up repository..."

# Make sure we have the latest changes
git add .
git commit -m "Update: Final repository setup and documentation" --allow-empty

echo
echo "🌐 Attempting to push to GitHub..."
echo "Repository: https://github.com/Irish3434/devlab.git"
echo

# Try to push
if git push -u origin main; then
    echo
    echo "✅ SUCCESS! Repository published to GitHub!"
    echo "🔗 View at: https://github.com/Irish3434/devlab"
    echo
    echo "📋 What was uploaded:"
    echo "  • Complete Picture Finder application"
    echo "  • Professional GUI with duplicate detection"
    echo "  • Comprehensive documentation"
    echo "  • MIT License"
    echo "  • Ready-to-run Python application"
    echo
else
    echo
    echo "🔑 Authentication needed!"
    echo
    echo "Choose your preferred method:"
    echo
    echo "Option 1 - Personal Access Token (Easiest):"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select 'repo' scope"
    echo "4. Copy the token"
    echo "5. Run: git push -u origin main"
    echo "6. Use your GitHub username and paste the token as password"
    echo
    echo "Option 2 - SSH Key (Most Secure):"
    echo "1. Copy this SSH key to GitHub:"
    cat ~/.ssh/id_ed25519.pub 2>/dev/null || echo "   (SSH key not found - run ssh-keygen first)"
    echo "2. Go to https://github.com/settings/ssh"
    echo "3. Add the key above"
    echo "4. Run: git remote set-url origin git@github.com:Irish3434/devlab.git"
    echo "5. Run: git push -u origin main"
    echo
fi

echo "📖 For detailed setup instructions, see: SETUP_GITHUB.md"