#!/bin/bash

# Deploy Focus Royale Backend to Railway
echo "🚂 Deploying Focus Royale Backend to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway authentication..."
railway whoami || railway login

# Initialize Railway project if needed
if [ ! -f "railway.toml" ]; then
    echo "📋 Initializing Railway project..."
    railway init
fi

# Set up environment variables
echo "⚙️ Setting up environment variables..."
echo "Please provide your MongoDB Atlas connection string:"
read -r MONGO_URL

echo "Please provide your database name (default: focus_royale):"
read -r DB_NAME
DB_NAME=${DB_NAME:-focus_royale}

# Set environment variables
railway variables set MONGO_URL="$MONGO_URL"
railway variables set DB_NAME="$DB_NAME"
railway variables set PORT="8000"

# Deploy to Railway
echo "🌟 Deploying to Railway..."
railway up

# Get the deployment URL
RAILWAY_URL=$(railway domain 2>/dev/null || echo "Please check your Railway dashboard for the URL")

echo "✅ Backend deployment completed!"
echo "🌐 Your backend API should be available at: $RAILWAY_URL"
echo "📋 Next steps for complete deployment:"
echo "   1. Deploy frontend to Vercel with REACT_APP_BACKEND_URL=$RAILWAY_URL"
echo "   2. Test your backend by visiting: $RAILWAY_URL/api/users"
echo "   3. Initialize the shop by visiting: $RAILWAY_URL/api/init"

# Optional: Deploy frontend to Vercel
echo ""
echo "🎯 Would you like to deploy the frontend to Vercel now? (y/n)"
read -r DEPLOY_FRONTEND

if [ "$DEPLOY_FRONTEND" = "y" ] || [ "$DEPLOY_FRONTEND" = "Y" ]; then
    echo "📦 Preparing frontend deployment..."
    
    # Update frontend environment
    echo "REACT_APP_BACKEND_URL=$RAILWAY_URL" > frontend/.env.production
    
    # Deploy frontend to Vercel
    if command -v vercel &> /dev/null; then
        echo "🚀 Deploying frontend to Vercel..."
        cd frontend
        vercel --prod
        cd ..
        echo "✅ Frontend deployed to Vercel!"
    else
        echo "❌ Vercel CLI not found. Please install it and deploy manually:"
        echo "   npm install -g vercel"
        echo "   cd frontend"
        echo "   vercel --prod"
    fi
fi