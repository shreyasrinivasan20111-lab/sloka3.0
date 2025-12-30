# Vercel Deployment Guide - jQuery Version

This is the **jQuery-based** Student Course Management System, ready for Vercel deployment.

## 📦 What's Included

This folder contains ONLY the essential files for Vercel deployment:

```
slokapp/
├── backend/                    # Python Flask backend
│   ├── __init__.py
│   ├── app.py                 # Main Flask app (port 8000)
│   ├── auth.py                # Authentication
│   ├── config.py              # Environment config
│   ├── database.py            # PostgreSQL schema
│   └── logger.py              # Logging system
├── frontend/                   # jQuery frontend
│   ├── index.html             # Main HTML (jQuery version)
│   └── static/
│       ├── css/
│       │   └── styles.css     # All styles
│       └── js/
│           └── app-jquery.js  # jQuery application
├── api/
│   └── index.py               # Vercel serverless entry
├── uploads/                    # File upload directory
├── logs/                       # Application logs
├── requirements.txt            # Python dependencies
├── vercel.json                # Vercel configuration
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # Main documentation
├── DEPLOYMENT.md              # General deployment guide
└── JQUERY_IMPLEMENTATION.md   # jQuery documentation
```

## 🚀 Quick Deployment to Vercel

### Prerequisites

- Vercel account (free): https://vercel.com/signup
- Git repository (GitHub, GitLab, or Bitbucket)

### Step 1: Push to Git Repository

```bash
cd /Users/kthiru6667/claudeprogs/slokapp

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - jQuery version for Vercel"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/slokapp.git

# Push
git push -u origin main
```

### Step 2: Deploy to Vercel

#### Option A: Using Vercel Dashboard (Recommended)

1. Go to https://vercel.com/new
2. Import your Git repository
3. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: (leave empty)
   - **Output Directory**: `frontend`
4. Add Environment Variables:
   - `SECRET_KEY` = (generate a random string)
   - `FLASK_ENV` = `production`
5. Click **Deploy**

#### Option B: Using Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: slokapp
# - Directory: ./ (current)

# Set environment variables
vercel env add SECRET_KEY
# Enter a random secret key (e.g., generated with: openssl rand -hex 32)

vercel env add FLASK_ENV
# Enter: production

# Deploy to production
vercel --prod
```

### Step 3: Access Your Application

After deployment, Vercel will provide a URL like:
```
https://slokapp.vercel.app
```

## 🔧 Environment Variables

Set these in Vercel dashboard (Settings → Environment Variables):

| Variable | Value | Required |
|----------|-------|----------|
| `SECRET_KEY` | Random string (32+ chars) | Yes |
| `FLASK_ENV` | `production` | Yes |
| `DB_PATH` | `/tmp/student_courses.db` | Auto-set |
| `UPLOAD_FOLDER` | `/tmp/uploads` | Auto-set |

### Generate SECRET_KEY

```bash
# Using Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL
openssl rand -hex 32

# Using Node
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## ⚙️ Configuration Files

### vercel.json

Already configured for this project:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

### api/index.py

Serverless entry point for Vercel:

```python
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set production environment
os.environ['FLASK_ENV'] = 'production'
os.environ['VERCEL'] = '1'

from backend.app import app
from backend.database import init_database

# Initialize database
try:
    init_database()
except Exception as e:
    print(f"Database initialization warning: {e}")

# Vercel handler
def handler(request, context):
    return app(request, context)
```

## ⚠️ Important Vercel Limitations

### 1. Ephemeral Filesystem

**Issue**: Files uploaded to `/tmp/` don't persist between requests

**Solutions**:
- **Development**: Local filesystem works fine
- **Production**: Use external storage:
  - AWS S3
  - Cloudinary
  - Vercel Blob Storage
  - Google Cloud Storage

### 2. Database Persistence

**Issue**: PostgreSQL configuration required for data persistence

**Solutions**:
- **Production**: PostgreSQL required for data persistence
- **Production**: Use external database:
  - PostgreSQL (Vercel Postgres, Supabase, Neon)
  - MongoDB (MongoDB Atlas)
  - MySQL (PlanetScale)

### 3. Function Timeout

**Issue**: Vercel functions timeout after 10 seconds (Hobby) or 60 seconds (Pro)

**Solution**: Optimize slow operations or upgrade plan

## 🔄 Updating Your Deployment

### Automatic Deployment (Recommended)

Vercel automatically deploys when you push to your Git repository:

```bash
# Make changes
git add .
git commit -m "Update: your changes"
git push

# Vercel will automatically deploy!
```

### Manual Deployment

```bash
# Deploy latest changes
vercel --prod
```

## 🧪 Testing Before Deployment

### Local Testing

```bash
cd /Users/kthiru6667/claudeprogs/slokapp

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -m backend.database

# Run locally
python3 -m backend.app

# Open http://localhost:8000
```

### Test Production Build

```bash
# Install Vercel CLI
npm install -g vercel

# Run locally with Vercel environment
vercel dev

# Access at http://localhost:3000
```

## 📊 Default Credentials

After deployment, use these credentials:

**Admin:**
- Email: `admin@example.com`
- Password: `admin123`

**Students:**
- Email: `student1@example.com` / Password: `student123`
- Email: `student2@example.com` / Password: `student123`

**⚠️ IMPORTANT**: Change these credentials in production!

## 🐛 Troubleshooting

### Build Fails

**Check:**
1. All files are committed to Git
2. `requirements.txt` is present
3. `vercel.json` is valid JSON
4. Python version compatibility

**Fix:**
```bash
# Verify files
git status

# Check Python dependencies
pip install -r requirements.txt

# Validate vercel.json
cat vercel.json | python3 -m json.tool
```

### Application Not Loading

**Check:**
1. Environment variables are set
2. `api/index.py` exists
3. Frontend files are in `frontend/`

**Fix:**
- Review Vercel deployment logs
- Check Functions tab in Vercel dashboard
- Verify all routes in `vercel.json`

### Database Errors

**Issue**: PostgreSQL DATABASE_URL required for production

**Temporary Fix** (Development):
- Database reinitializes on each cold start
- Sample data is recreated

**Permanent Fix** (Production):
- Migrate to PostgreSQL or MongoDB
- Update `backend/database.py` to use new database

### File Upload Not Working

**Issue**: Uploaded files don't persist

**Fix**: Implement external storage (see Limitations above)

## 📝 Deployment Checklist

Before deploying:

- [ ] All files committed to Git
- [ ] `.env` file NOT committed (only `.env.example`)
- [ ] `SECRET_KEY` generated and added to Vercel
- [ ] Database sample data acceptable for production
- [ ] Default passwords documented (or changed)
- [ ] Error logging configured
- [ ] CORS origins updated for production domain

## 🔗 Useful Links

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Vercel Docs**: https://vercel.com/docs
- **Vercel Python Runtime**: https://vercel.com/docs/functions/runtimes/python
- **Vercel Environment Variables**: https://vercel.com/docs/environment-variables

## 📞 Support

If deployment fails:

1. Check Vercel deployment logs
2. Review this guide
3. Check `DEPLOYMENT.md` for detailed info
4. Review `README.md` for application details

## ✅ Success Criteria

Your deployment is successful when:

1. ✅ Vercel deployment shows "Ready"
2. ✅ URL is accessible
3. ✅ Login page loads without errors
4. ✅ Can login as admin/student
5. ✅ Can view courses
6. ✅ No console errors

## 🎉 Next Steps After Deployment

1. **Test thoroughly**: Login, create courses, assign students
2. **Update credentials**: Change default admin password
3. **Setup external database**: For production persistence
4. **Setup external storage**: For file uploads
5. **Add custom domain**: In Vercel settings
6. **Monitor logs**: Check Vercel functions logs

---

**Your jQuery-based Student Course Management System is ready for Vercel!** 🚀

Deploy it and enjoy your cloud-hosted application!
