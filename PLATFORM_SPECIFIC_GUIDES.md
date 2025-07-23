# Platform-Specific Deployment Guides

## Quick Start Commands

```bash
# Make scripts executable
chmod +x deploy-vercel.sh deploy-railway.sh

# Deploy to Vercel (Full-stack)
./deploy-vercel.sh

# Deploy to Railway (Backend) + Vercel (Frontend)
./deploy-railway.sh

# Local development with Docker
docker-compose up -d
```

## 1. Vercel Deployment (Recommended for Full-Stack)

### Prerequisites
- Node.js 16+ installed
- Vercel CLI: `npm install -g vercel`
- MongoDB Atlas account

### Step-by-step Deployment

1. **Prepare MongoDB Atlas**
   ```bash
   # Get your connection string from MongoDB Atlas
   # Format: mongodb+srv://username:password@cluster.mongodb.net/dbname
   ```

2. **Run Deployment Script**
   ```bash
   ./deploy-vercel.sh
   ```

3. **Manual Alternative**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Login to Vercel
   vercel login
   
   # Deploy
   vercel --prod
   
   # Set environment variables in Vercel dashboard
   ```

### Environment Variables for Vercel
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/focus_royale
DB_NAME=focus_royale
REACT_APP_BACKEND_URL=https://your-project.vercel.app
```

### Vercel Configuration Files
- `/vercel.json` - Main Vercel configuration
- `/frontend/vercel.json` - Frontend-specific configuration
- `/backend/vercel_app.py` - Serverless function wrapper
- `/backend/requirements-vercel.txt` - Python dependencies with Mangum

## 2. Railway Deployment (Best for Scalable Backend)

### Prerequisites
- Railway CLI: `npm install -g @railway/cli`
- MongoDB Atlas account

### Step-by-step Deployment

1. **Deploy Backend to Railway**
   ```bash
   ./deploy-railway.sh
   ```

2. **Deploy Frontend to Vercel**
   ```bash
   cd frontend
   echo "REACT_APP_BACKEND_URL=https://your-railway-backend.up.railway.app" > .env.production
   vercel --prod
   ```

### Manual Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Set environment variables
railway variables set MONGO_URL="your-mongo-url"
railway variables set DB_NAME="focus_royale"
railway variables set PORT="8000"

# Deploy
railway up
```

### Railway Configuration Files
- `/railway.json` - Railway service configuration
- `/railway.toml` - Build and deploy settings
- `/Procfile` - Process definition for Railway

## 3. MongoDB Atlas Setup (Required for All Deployments)

### Quick Setup Steps

1. **Create Account & Cluster**
   - Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Create free M0 cluster

2. **Database Access**
   ```
   Username: focus_royale_user
   Password: [generate strong password]
   Role: Read and write to any database
   ```

3. **Network Access**
   ```
   IP Address: 0.0.0.0/0 (Allow from anywhere)
   ```

4. **Connection String**
   ```
   mongodb+srv://focus_royale_user:password@cluster0.xxxxx.mongodb.net/focus_royale?retryWrites=true&w=majority
   ```

## 4. Docker Deployment (Local Development)

### Prerequisites
- Docker and Docker Compose installed

### Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services
docker-compose build
```

### Services Included
- **MongoDB**: Local database instance
- **Backend**: FastAPI server
- **Frontend**: React development server

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- MongoDB: localhost:27017

## 5. Environment Variables Reference

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://your-backend-url
WDS_SOCKET_PORT=443  # For Vercel WebSocket
```

### Backend (.env)
```bash
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/dbname
DB_NAME=focus_royale
PORT=8000  # For Railway/Docker
```

## 6. Post-Deployment Steps

### Initialize Application
```bash
# Initialize shop items (run once)
curl -X POST https://your-backend-url/api/init

# Test user registration
curl -X POST https://your-backend-url/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

### Verify Deployment
1. Visit your frontend URL
2. Register a new user
3. Start a focus session
4. Check MongoDB Atlas for data
5. Test shop functionality

## 7. Platform Comparison

| Feature | Vercel | Railway | Docker |
|---------|--------|---------|--------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost (Free Tier)** | Generous | Good | Free |
| **Scalability** | Excellent | Excellent | Manual |
| **Performance** | Fast (Edge) | Fast | Local |
| **Best For** | Full-stack MVPs | Backend APIs | Development |

## 8. Troubleshooting Common Issues

### Build Failures
```bash
# Clear build cache
vercel --force  # Vercel
railway up --detach  # Railway

# Check build logs
vercel logs  # Vercel
railway logs  # Railway
```

### Database Connection Issues
```bash
# Test MongoDB connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('your-mongo-url').admin.command('ismaster'))"
```

### CORS Issues
```bash
# Check if API endpoints are accessible
curl -H "Origin: https://your-frontend-url" https://your-backend-url/api/users
```

### Environment Variable Issues
```bash
# Verify environment variables are set
vercel env ls  # Vercel
railway variables  # Railway
```

## 9. Monitoring and Maintenance

### Performance Monitoring
- Vercel Analytics: Built-in performance metrics
- Railway Metrics: CPU, memory, and request tracking
- MongoDB Atlas: Database performance monitoring

### Log Monitoring
```bash
# Real-time logs
vercel logs --follow
railway logs --follow
docker-compose logs -f
```

### Health Checks
```bash
# Backend health check
curl https://your-backend-url/api/users

# Database health check
curl https://your-backend-url/api/init
```

## 10. Security Best Practices

### Environment Variables
- Never commit `.env` files to version control
- Use platform secret management systems
- Rotate database passwords regularly

### Database Security
- Use strong passwords
- Enable MongoDB Atlas IP whitelisting when possible
- Monitor database access logs

### API Security
- Implement rate limiting in production
- Use HTTPS for all deployments
- Monitor for unusual API usage patterns

---

Choose the deployment option that best fits your needs:
- **Vercel**: Best for quick full-stack deployment
- **Railway + Vercel**: Best for scalable production apps
- **Docker**: Best for local development and testing