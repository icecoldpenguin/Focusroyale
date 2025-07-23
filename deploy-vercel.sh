#!/bin/bash

# Deploy Focus Royale to Vercel
echo "🚀 Deploying Focus Royale to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Login to Vercel (if not already logged in)
echo "🔐 Checking Vercel authentication..."
vercel whoami || vercel login

# Set up environment variables
echo "⚙️ Setting up environment variables..."
echo "Please provide your MongoDB Atlas connection string:"
read -r MONGO_URL

echo "Please provide your database name (default: focus_royale):"
read -r DB_NAME
DB_NAME=${DB_NAME:-focus_royale}

# Create .env.production file for the build
echo "REACT_APP_BACKEND_URL=" > frontend/.env.production

# Deploy to Vercel
echo "🌟 Deploying to Vercel..."
vercel --prod

# Get the deployment URL
DEPLOYMENT_URL=$(vercel ls --scope=team 2>/dev/null | grep "https://" | head -1 | awk '{print $2}' || echo "Please check your Vercel dashboard for the URL")

# Update environment variables with the actual URL
if [ "$DEPLOYMENT_URL" != "Please check your Vercel dashboard for the URL" ]; then
    echo "REACT_APP_BACKEND_URL=$DEPLOYMENT_URL" > frontend/.env.production
    
    # Set environment variables in Vercel
    vercel env add MONGO_URL production <<< "$MONGO_URL"
    vercel env add DB_NAME production <<< "$DB_NAME"
    vercel env add REACT_APP_BACKEND_URL production <<< "$DEPLOYMENT_URL"
    
    # Redeploy with correct environment variables
    echo "🔄 Redeploying with correct environment variables..."
    vercel --prod
fi

echo "✅ Deployment completed!"
echo "🌐 Your app should be available at: $DEPLOYMENT_URL"
echo "📋 Next steps:"
echo "   1. Test your deployment by visiting the URL above"
echo "   2. Initialize the shop by visiting: $DEPLOYMENT_URL/api/init"
echo "   3. Register a new user to test the full functionality"