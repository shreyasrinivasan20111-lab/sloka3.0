# Production Deployment Guide

This guide covers deploying the Student Course Management System to production, with a focus on Vercel deployment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Vercel Deployment](#vercel-deployment)
3. [Environment Variables](#environment-variables)
4. [Production Considerations](#production-considerations)
5. [Alternative Deployment Options](#alternative-deployment-options)

---

## Prerequisites

### Required
- Git repository (GitHub, GitLab, or Bitbucket)
- Vercel account (free tier available at [vercel.com](https://vercel.com))
- Python 3.9+

### Recommended
- Custom domain (optional, Vercel provides free subdomain)
- Cloud storage service for file uploads (see [File Storage](#file-storage))
- Cloud database for production (see [Database Options](#database-options))

---

## Vercel Deployment

### Step 1: Prepare Your Repository

1. **Initialize Git (if not already done):**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Production ready"
   ```

2. **Push to GitHub:**
   ```bash
   gh repo create student-course-management --public
   git remote add origin https://github.com/YOUR_USERNAME/student-course-management.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Vercel

#### Option A: Using Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? **Y**
   - Which scope? Select your account
   - Link to existing project? **N**
   - Project name? `student-course-management`
   - Directory? `./` (current directory)
   - Override settings? **N**

5. **Set environment variables:**
   ```bash
   vercel env add SECRET_KEY
   ```
   Enter a secure secret key when prompted (generate one with `python -c "import secrets; print(secrets.token_hex(32))"`)

6. **Deploy to production:**
   ```bash
   vercel --prod
   ```

#### Option B: Using Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository
3. Configure project:
   - **Framework Preset:** Other
   - **Root Directory:** `./`
   - **Build Command:** (leave empty)
   - **Output Directory:** `frontend`
4. Add environment variables (see [Environment Variables](#environment-variables))
5. Click **Deploy**

### Step 3: Configure Environment Variables in Vercel

Add these environment variables in Vercel Dashboard (Settings → Environment Variables):

| Variable | Value | Required |
|----------|-------|----------|
| `FLASK_ENV` | `production` | Yes |
| `SECRET_KEY` | Your secret key | Yes |
| `CORS_ORIGINS` | `*` or your domain | No |

**Generate a SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Environment Variables

### Development (.env file)

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**
   ```bash
   FLASK_ENV=development
   SECRET_KEY=your-dev-secret-key
   DB_PATH=student_courses.db
   UPLOAD_FOLDER=uploads
   CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
   ```

### Production (Vercel)

Set via Vercel CLI or Dashboard:
```bash
vercel env add SECRET_KEY production
vercel env add FLASK_ENV production
vercel env add CORS_ORIGINS production
```

---

## Production Considerations

### ⚠️ Important Limitations on Vercel

Vercel's serverless functions have limitations:

1. **Ephemeral Filesystem**
   - Files uploaded during runtime are **not persisted** between requests
   - The `/tmp` directory is cleared between function invocations
   - **Solution:** Use cloud storage (see below)

2. **Database Persistence**
   - PostgreSQL DATABASE_URL must be configured for data persistence
   - **Solution:** Use cloud database or keep for demo purposes only

3. **Function Timeout**
   - Maximum execution time: 10 seconds (free tier), 60 seconds (pro)
   - **Solution:** Optimize database queries and file operations

### File Storage

For production, replace local file storage with a cloud service:

#### Option 1: AWS S3
```bash
pip install boto3
```

#### Option 2: Cloudinary (Recommended for simplicity)
```bash
pip install cloudinary
```

#### Option 3: Vercel Blob Storage
```bash
pip install @vercel/blob
```

**Implementation Note:** Modify `backend/app.py` upload functions to use your chosen storage service.

### Database Options

#### Option 1: PostgreSQL (Recommended)
Use services like:
- [Supabase](https://supabase.com) (Free tier available)
- [Neon](https://neon.tech) (Serverless PostgreSQL)
- [Railway](https://railway.app) (PostgreSQL hosting)

**Migration steps:**
1. Configure PostgreSQL with DATABASE_URL environment variable
2. Update `backend/database.py` with PostgreSQL connection
3. Adjust SQL syntax for PostgreSQL compatibility

#### Option 2: MongoDB
Use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (Free tier available)

#### PostgreSQL Production Setup
- Acceptable for demos and testing
- Database resets on each deployment
- Add initialization check to populate sample data

### Security Enhancements

1. **Generate Strong Secret Key:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Update CORS Origins:**
   ```python
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

3. **Enable HTTPS Only:**
   - Vercel provides HTTPS by default
   - Enforce HTTPS in your application

4. **Add Rate Limiting:**
   ```bash
   pip install flask-limiter
   ```

5. **Implement CSRF Protection:**
   ```bash
   pip install flask-wtf
   ```

### Session Management

For distributed environments, use Redis or database-backed sessions:

```bash
pip install flask-session redis
```

Update `backend/app.py`:
```python
from flask_session import Session
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL'))
Session(app)
```

---

## Alternative Deployment Options

### Option 1: Traditional Server (VPS)

**Providers:** DigitalOcean, Linode, AWS EC2, Google Cloud

**Setup:**
1. Install Python and dependencies
2. Use Gunicorn as WSGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
   ```
3. Set up Nginx as reverse proxy
4. Use systemd for process management
5. Configure SSL with Let's Encrypt

### Option 2: Docker Deployment

**Create Dockerfile:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app"]
```

**Deploy to:**
- Docker Hub + any VPS
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances

### Option 3: Heroku

1. Create `Procfile`:
   ```
   web: gunicorn backend.app:app
   ```

2. Create `runtime.txt`:
   ```
   python-3.9.18
   ```

3. Deploy:
   ```bash
   heroku create student-course-management
   heroku config:set SECRET_KEY=your-secret-key
   git push heroku main
   ```

### Option 4: Railway.app

1. Connect GitHub repository
2. Configure environment variables
3. Deploy automatically on push

---

## Testing Production Deployment

### Before Deployment Checklist

- [ ] All environment variables configured
- [ ] SECRET_KEY is strong and secure
- [ ] CORS origins properly set
- [ ] Database connection tested
- [ ] File upload/download working
- [ ] Authentication tested
- [ ] All API endpoints working

### After Deployment Checklist

- [ ] Application loads correctly
- [ ] Login functionality works
- [ ] Course creation works (admin)
- [ ] Course viewing works (student)
- [ ] File uploads work (if implemented)
- [ ] HTTPS enabled
- [ ] Custom domain configured (if applicable)

### Testing Commands

```bash
# Test login endpoint
curl -X POST https://your-domain.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test course list (requires authentication)
curl https://your-domain.com/api/courses \
  -H "Cookie: session=your-session-cookie"
```

---

## Monitoring and Maintenance

### Vercel Monitoring

- View logs: `vercel logs`
- Check deployment status: Dashboard → Deployments
- Monitor function invocations: Dashboard → Analytics

### Recommended Tools

- **Error Tracking:** Sentry, Rollbar
- **Uptime Monitoring:** UptimeRobot, Pingdom
- **Performance:** Vercel Analytics, Google Analytics

### Updating the Application

```bash
# Make changes
git add .
git commit -m "Update: description"
git push origin main

# Vercel auto-deploys on push
# Or manually deploy:
vercel --prod
```

---

## Troubleshooting

### Common Issues

**1. 502 Bad Gateway**
- Check function logs: `vercel logs`
- Verify all environment variables are set
- Check for syntax errors in code

**2. Database Connection Fails**
- Verify database URL is correct
- Check firewall rules
- Ensure database service is running

**3. File Uploads Not Working**
- Implement cloud storage (S3, Cloudinary)
- Check file size limits
- Verify permissions

**4. Session Issues**
- Use database or Redis-backed sessions
- Check SECRET_KEY is set
- Verify cookies are sent with requests

**5. CORS Errors**
- Add your domain to CORS_ORIGINS
- Check credentials are included in requests
- Verify preflight requests succeed

### Getting Help

- Vercel Documentation: [vercel.com/docs](https://vercel.com/docs)
- Flask Documentation: [flask.palletsprojects.com](https://flask.palletsprojects.com)
- Community Support: [vercel.com/support](https://vercel.com/support)

---

## Cost Estimates

### Vercel (Free Tier)
- ✅ 100GB bandwidth/month
- ✅ Unlimited static deployments
- ✅ Serverless function executions (limited)
- ✅ HTTPS included
- ❌ File persistence (need external storage)

### Recommended Production Stack (Free Tier)
- **Hosting:** Vercel (Free)
- **Database:** Supabase PostgreSQL (Free - 500MB)
- **File Storage:** Cloudinary (Free - 25GB/month)
- **Total Cost:** $0/month

### Scalable Production Stack
- **Hosting:** Vercel Pro ($20/month)
- **Database:** Neon PostgreSQL ($0-19/month)
- **File Storage:** AWS S3 (~$0.023/GB)
- **Total Cost:** ~$20-50/month depending on usage

---

## Next Steps

1. ✅ Complete this deployment guide
2. Test locally with production settings
3. Deploy to Vercel
4. Configure custom domain (optional)
5. Set up monitoring and alerts
6. Implement cloud storage (if needed)
7. Migrate to production database (if needed)
8. Add additional security features

**Your application is now production-ready! 🚀**
