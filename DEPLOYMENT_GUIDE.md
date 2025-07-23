# Focus Royale - Deployment Guide

This guide provides step-by-step instructions for deploying your Focus Royale application on Vercel, Railway, and MongoDB Atlas.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [MongoDB Atlas Setup](#mongodb-atlas-setup)
3. [Vercel Deployment (Full-Stack)](#vercel-deployment-full-stack)
4. [Railway Deployment (Backend Only)](#railway-deployment-backend-only)
5. [Environment Configuration](#environment-configuration)
6. [Testing Deployments](#testing-deployments)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:
- GitHub account
- Vercel account
- Railway account
- MongoDB Atlas account (free tier available)

## MongoDB Atlas Setup

### 1. Create MongoDB Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Sign up or log in to your account
3. Click "Create a New Cluster"
4. Choose the free M0 tier
5. Select your preferred cloud provider and region
6. Click "Create Cluster"

### 2. Configure Database Access

1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Create a user with username and password
4. Select "Read and write to any database"
5. Click "Add User"

### 3. Configure Network Access

1. Go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

### 4. Get Connection String

1. Go to "Clusters" and click "Connect"
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your database user password
5. Replace `<dbname>` with your preferred database name (e.g., `focus_royale`)

Example connection string:
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/focus_royale?retryWrites=true&w=majority
```

## Vercel Deployment (Full-Stack)

### 1. Prepare Your Repository

1. Push your code to GitHub
2. Ensure all files from this guide are included

### 2. Deploy to Vercel

1. Go to [Vercel](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: Leave empty (.)
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/build`
   - **Install Command**: `cd frontend && npm install`

### 3. Set Environment Variables

In Vercel dashboard, go to Settings > Environment Variables and add:

```
MONGO_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/focus_royale?retryWrites=true&w=majority
DB_NAME=focus_royale
REACT_APP_BACKEND_URL=https://your-project-name.vercel.app
```

### 4. Deploy

1. Click "Deploy"
2. Wait for deployment to complete
3. Your app will be available at `https://your-project-name.vercel.app`

## Railway Deployment (Backend Only)

### 1. Deploy Backend to Railway

1. Go to [Railway](https://railway.app)
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect the Python app

### 2. Configure Environment Variables

In Railway dashboard, go to Variables tab and add:

```
MONGO_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/focus_royale?retryWrites=true&w=majority
DB_NAME=focus_royale
PORT=8000
```

### 3. Configure Start Command

If Railway doesn't auto-detect, set the start command:
```
cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
```

### 4. Deploy Frontend Separately

For Railway backend + separate frontend:

1. Deploy frontend to Vercel (steps above, but simpler)
2. Set `REACT_APP_BACKEND_URL` to your Railway backend URL
3. Example: `https://your-backend.up.railway.app`

## Environment Configuration

### Frontend Environment Variables (.env)

```bash
# For Vercel full-stack deployment
REACT_APP_BACKEND_URL=https://your-project.vercel.app

# For Railway backend + Vercel frontend
REACT_APP_BACKEND_URL=https://your-backend.up.railway.app
```

### Backend Environment Variables (.env)

```bash
MONGO_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/focus_royale?retryWrites=true&w=majority
DB_NAME=focus_royale

# Railway only
PORT=8000
```

## Testing Deployments

### 1. Test Backend API

Test these endpoints:
```bash
# Health check
curl https://your-backend-url/api/users

# Initialize shop
curl -X POST https://your-backend-url/api/init
```

### 2. Test Frontend

1. Open your deployed frontend URL
2. Try to register a new user
3. Create a focus session
4. Check if data persists

### 3. Test Database Connection

1. Register multiple users
2. Check MongoDB Atlas dashboard
3. Go to Collections tab
4. Verify data is being stored

## Advanced Configuration

### Custom Domain (Vercel)

1. Go to your project settings in Vercel
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

### Auto-deployments

Configure automatic deployments:
1. Connect your repository to the deployment platform
2. Set up branch-based deployments
3. Configure deployment triggers

### Environment-specific Configurations

Create separate environments:
- `production` - Live application
- `staging` - Testing environment
- `development` - Local development

## Monitoring and Logs

### Vercel Logs
- Go to your project dashboard
- Click "Functions" tab
- View serverless function logs

### Railway Logs
- Go to your project dashboard
- Click "Logs" tab
- Monitor real-time application logs

### MongoDB Atlas Monitoring
- Use Atlas monitoring dashboard
- Set up alerts for database performance
- Monitor connection counts and queries

## Troubleshooting

### Common Issues

**CORS Errors:**
- Ensure CORS is properly configured in FastAPI
- Check if frontend URL is in allowed origins

**Database Connection:**
- Verify MongoDB Atlas IP whitelist
- Check connection string format
- Ensure database user has proper permissions

**Build Failures:**
- Check build logs for missing dependencies
- Verify all required files are in repository
- Check Node.js/Python versions

**Environment Variables:**
- Ensure all required variables are set
- Check for typos in variable names
- Verify secrets are properly configured

### Getting Help

1. Check platform-specific documentation:
   - [Vercel Docs](https://vercel.com/docs)
   - [Railway Docs](https://docs.railway.app)
   - [MongoDB Atlas Docs](https://docs.atlas.mongodb.com)

2. Common debugging commands:
```bash
# Check frontend build
cd frontend && npm run build

# Test backend locally
cd backend && uvicorn server:app --reload

# Test MongoDB connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('Connection OK')"
```

## Security Considerations

1. **Environment Variables**: Never commit sensitive data to your repository
2. **Database Security**: Use strong passwords and IP restrictions
3. **HTTPS**: Ensure all deployments use HTTPS
4. **API Rate Limiting**: Consider implementing rate limiting for production

## Scaling Considerations

1. **Database**: MongoDB Atlas auto-scales based on usage
2. **Backend**: Railway and Vercel handle auto-scaling
3. **Frontend**: Vercel Edge Network provides global CDN
4. **Monitoring**: Set up alerts for high usage periods

---

Your Focus Royale application is now ready for deployment! Choose the platform that best fits your needs and follow the corresponding section above.