# SLOKAPP - Student Course Management System (jQuery + Vercel Ready)

## 🎯 What is This?

This is a **clean, deployment-ready** version of the Student Course Management System using **jQuery** for the frontend, prepared specifically for **Vercel deployment**.

## ✨ Features

- **jQuery Frontend** - Clean, concise code (~800 lines)
- **Flask Backend** - Python with REST API
- **DuckDB Database** - Embedded SQL database
- **Quill.js Editor** - Rich text for course content
- **File Management** - Upload/download course materials
- **Role-Based Access** - Admin and Student roles
- **Email Authentication** - Email-based login
- **Student Signup** - Self-registration
- **Course Assignment** - Assign courses to students
- **Comprehensive Logging** - Track all activities
- **Error Handling** - User-friendly error messages

## 📁 Project Structure

```
slokapp/
├── backend/               # Python Flask backend
├── frontend/              # jQuery frontend (ONLY jQuery, no React/Vanilla)
├── api/                   # Vercel serverless entry
├── uploads/               # File uploads
├── logs/                  # Application logs
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel configuration
└── Documentation files
```

## 🚀 Quick Start

### Local Development

```bash
cd /Users/kthiru6667/claudeprogs/slokapp

# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python3 -m backend.database

# 3. Run application
python3 -m backend.app

# 4. Open browser
open http://localhost:8000
```

### Deploy to Vercel

```bash
# 1. Initialize git
git init
git add .
git commit -m "Initial commit"

# 2. Push to GitHub
# (Create repo on GitHub first)
git remote add origin https://github.com/YOUR_USERNAME/slokapp.git
git push -u origin main

# 3. Deploy to Vercel
# Go to https://vercel.com/new
# Import your GitHub repository
# Set environment variables:
#   - SECRET_KEY (generate random string)
#   - FLASK_ENV = production
# Click Deploy!
```

## 🔑 Default Credentials

**Admin:**
- Email: `admin@example.com`
- Password: `admin123`

**Students:**
- Email: `student1@example.com` / Password: `student123`
- Email: `student2@example.com` / Password: `student123`

## 📚 Documentation

| File | Description |
|------|-------------|
| **VERCEL_DEPLOYMENT.md** | Complete Vercel deployment guide |
| **README.md** | Full application documentation |
| **DEPLOYMENT.md** | General deployment guide |
| **JQUERY_IMPLEMENTATION.md** | jQuery implementation details |

## ✅ What's Included (jQuery Only)

### Frontend
- ✅ `index.html` - jQuery version (from index-jquery.html)
- ✅ `app-jquery.js` - jQuery implementation
- ✅ `styles.css` - All styles
- ❌ No React files
- ❌ No Vanilla JS files
- ❌ No backup files

### Backend
- ✅ `app.py` - Flask app with all endpoints
- ✅ `auth.py` - Authentication
- ✅ `config.py` - Environment configuration
- ✅ `database.py` - DuckDB schema
- ✅ `logger.py` - Logging system
- ✅ Port 8000 configured

### Configuration
- ✅ `vercel.json` - Vercel deployment config
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.example` - Environment template
- ✅ `.gitignore` - Git ignore rules
- ✅ `api/index.py` - Vercel serverless entry

## 🎯 Key Fixes Included

This version includes all the latest fixes:

1. ✅ **Port 8000** - Changed from 5000 (macOS AirPlay conflict)
2. ✅ **Check-Auth Endpoint** - Added `/api/check-auth`
3. ✅ **Student Courses Fix** - Students can see assigned courses
4. ✅ **Assignment Modal** - Loads current assignments correctly
5. ✅ **Unique Element IDs** - Fixed duplicate ID conflicts

## 🔧 Technology Stack

- **Frontend**: jQuery 3.7.1, HTML5, CSS3
- **Backend**: Python 3.9+, Flask 3.0+
- **Database**: DuckDB 0.9.0+ (embedded)
- **Rich Text**: Quill.js 1.3.6
- **Deployment**: Vercel-ready serverless

## 📊 File Count

```
Total files: ~20 essential files
Backend: 6 files
Frontend: 3 files (HTML + JS + CSS)
Config: 4 files
Docs: 4 files
API: 1 file
```

## ⚡ Why This Version?

### Clean
- No backup files
- No multiple frontend versions
- No development files
- No log/database files

### Complete
- All features working
- All fixes applied
- All documentation included
- Ready to deploy

### Optimized
- Only jQuery (no React/Vanilla JS overhead)
- Small bundle size (~30KB jQuery)
- Clean, concise code (~800 lines)
- Fast performance

## 🚨 Important Notes

### For Production Deployment

1. **Database Persistence**: DuckDB doesn't persist on Vercel
   - Data reinitializes on each cold start
   - For production, migrate to PostgreSQL/MongoDB

2. **File Uploads**: Files don't persist on Vercel
   - Use external storage (S3, Cloudinary, etc.)

3. **Environment Variables**: Set in Vercel dashboard
   - `SECRET_KEY` - Generate random string
   - `FLASK_ENV` - Set to "production"

### For Development

- Works perfectly on local machine
- Database persists locally
- File uploads persist locally
- No external services needed

## 🎓 Next Steps

### 1. Local Testing (Recommended First)
```bash
cd /Users/kthiru6667/claudeprogs/slokapp
pip install -r requirements.txt
python3 -m backend.database
python3 -m backend.app
```

### 2. Deploy to Vercel
Follow `VERCEL_DEPLOYMENT.md` for step-by-step instructions

### 3. Test Deployment
- Login as admin
- Create a course
- Assign to students
- Login as student
- Verify courses appear

## 📞 Support

If you encounter issues:

1. Check `VERCEL_DEPLOYMENT.md` for Vercel-specific issues
2. Check `README.md` for general application info
3. Check `JQUERY_IMPLEMENTATION.md` for jQuery details
4. Review Vercel deployment logs

## ✅ Pre-Deployment Checklist

Before deploying to Vercel:

- [ ] Tested locally and everything works
- [ ] Git repository created and pushed
- [ ] Environment variables ready (SECRET_KEY)
- [ ] Understand Vercel limitations (ephemeral storage)
- [ ] Default credentials acceptable or documented

## 🎉 Ready!

This folder contains everything you need to deploy to Vercel.

**Next:** Follow `VERCEL_DEPLOYMENT.md` for deployment instructions!

---

**Clean. Complete. Ready to Deploy.** 🚀
