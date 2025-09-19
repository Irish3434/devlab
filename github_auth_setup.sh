#!/bin/bash

# GitHub Authentication Helper for Picture Finder
# This script helps set up proper authentication with GitHub

echo "🔐 GitHub Authentication Setup for Picture Finder"
echo "=================================================="
echo ""
echo "⚠️  IMPORTANT: GitHub no longer accepts passwords for Git operations."
echo "   You must use a Personal Access Token instead."
echo ""
echo "📝 To create a Personal Access Token:"
echo "   1. Go to: https://github.com/settings/tokens"
echo "   2. Click 'Generate new token (classic)'"
echo "   3. Name: 'Picture Finder Development'"
echo "   4. Select these scopes:"
echo "      ✅ repo (Full control of private repositories)"
echo "      ✅ workflow (Update GitHub Action workflows)"
echo "      ✅ write:packages (Upload packages)"
echo "   5. Click 'Generate token'"
echo "   6. Copy the token (starts with ghp_)"
echo ""

# Function to test if a token works
test_token() {
    local token=$1
    if [ -z "$token" ]; then
        echo "❌ No token provided"
        return 1
    fi
    
    echo "🧪 Testing token..."
    response=$(curl -s -H "Authorization: token $token" https://api.github.com/user)
    
    if echo "$response" | grep -q '"login"'; then
        username=$(echo "$response" | grep '"login"' | cut -d'"' -f4)
        echo "✅ Token is valid for user: $username"
        return 0
    else
        echo "❌ Token is invalid or expired"
        return 1
    fi
}

# Function to set up git with token
setup_git_auth() {
    local username=$1
    local token=$2
    
    echo "🔧 Setting up Git authentication..."
    
    # Set the remote URL with embedded token
    git remote set-url origin "https://${username}:${token}@github.com/Irish3434/devlab.git"
    
    # Configure git user
    git config --local user.name "$username"
    git config --local user.email "${username}@users.noreply.github.com"
    
    echo "✅ Git authentication configured"
}

# Function to push to GitHub
push_to_github() {
    echo "🚀 Pushing to GitHub..."
    
    if git push -u origin main; then
        echo "🎉 Successfully pushed to GitHub!"
        echo "🌟 Repository: https://github.com/Irish3434/devlab"
        
        # Clean up credentials from URL for security
        git remote set-url origin "https://github.com/Irish3434/devlab.git"
        echo "🔒 Cleaned up embedded credentials"
        
        return 0
    else
        echo "❌ Push failed"
        return 1
    fi
}

# Main execution
echo "💡 If you already have a Personal Access Token, enter it below:"
echo "   (Or press Enter to get instructions for creating one)"
echo ""
read -p "🔑 Enter your Personal Access Token: " -s user_token
echo ""

if [ -n "$user_token" ]; then
    if test_token "$user_token"; then
        setup_git_auth "Irish3434" "$user_token"
        push_to_github
    else
        echo "❌ Please create a new token with proper scopes"
        echo "🔗 Visit: https://github.com/settings/tokens"
    fi
else
    echo ""
    echo "📖 Instructions to create a Personal Access Token:"
    echo ""
    echo "1. Open in browser: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Fill in:"
    echo "   Name: Picture Finder Development"
    echo "   Expiration: 30 days (or your preference)"
    echo "   Scopes: ✅ repo, ✅ workflow, ✅ write:packages"
    echo "4. Click 'Generate token'"
    echo "5. Copy the token (starts with ghp_)"
    echo "6. Run this script again and paste the token"
    echo ""
    echo "🔒 Security Note: Never share your token or commit it to code!"
fi

echo ""
echo "🆘 Need help? The token replaces your GitHub password for Git operations."
echo "   Username: Irish3434"
echo "   Password: [Your Personal Access Token]"