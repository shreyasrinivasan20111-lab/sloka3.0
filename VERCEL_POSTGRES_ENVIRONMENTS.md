# 🗄️ Vercel PostgreSQL Environment Setup Guide

This guide helps you set up **two separate Vercel PostgreSQL databases** - one for development/testing and one for production.

## 🎯 **Overview**

We'll create:
- **Development Database**: For local testing and development
- **Production Database**: For live deployment

Both will use Vercel PostgreSQL for consistency and reliability.

---

## 🚀 **Step 1: Create Development Database**

### **1.1 Create Development Project (Optional)**
```bash
# Create a separate Vercel project for development (recommended)
vercel project add sloka-dev
```

### **1.2 Set up Development PostgreSQL**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to your **development project** (or main project)
3. Go to **Storage** → **Create Database** → **PostgreSQL**
4. Name it: `sloka-development-db`
5. Select region closest to you
6. Click **Create**

### **1.3 Get Development DATABASE_URL**
1. In your development database dashboard
2. Go to **Settings** tab
3. Copy the **DATABASE_URL** (starts with `postgresql://`)
4. Save it for local environment setup

---

## 🏭 **Step 2: Create Production Database**

### **2.1 Set up Production PostgreSQL**
1. Go to your **production Vercel project**
2. Go to **Storage** → **Create Database** → **PostgreSQL**  
3. Name it: `sloka-production-db`
4. Select region closest to your users
5. Click **Create**

### **2.2 Connect to Production Project**
1. In the production database dashboard
2. Go to **Settings** → **Connect Project**
3. Select your production Vercel project
4. Click **Connect**

This automatically adds `DATABASE_URL` to your production environment variables.

---

## 🔧 **Step 3: Configure Local Development**

### **3.1 Update Local Environment**
Create/update `.env.local`:

```bash
# Copy the template
cp .env.local.example .env.local

# Edit with your development database URL
FLASK_ENV=development
SECRET_KEY=your-dev-secret-key
DATABASE_URL=postgresql://your-dev-database-url-here
DEBUG=true
LOG_LEVEL=DEBUG
```

### **3.2 Test Local Connection**
```bash
# Test database connection
python3 -c "
from backend.database import get_connection, init_database
try:
    conn = get_connection()
    print('✅ Database connection successful!')
    conn.close()
    init_database()
    print('✅ Database initialization complete!')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

---

## 🌐 **Step 4: Configure Production Environment**

### **4.1 Set Production Environment Variables**
In your Vercel project dashboard → **Settings** → **Environment Variables**:

```bash
# Required Production Variables
SECRET_KEY=your-super-secure-production-secret-key
FLASK_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Optional Production Variables
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
UPLOAD_FOLDER=/tmp/uploads
```

### **4.2 Verify DATABASE_URL**
1. Go to **Settings** → **Environment Variables**
2. Confirm `DATABASE_URL` is automatically set by Vercel Postgres
3. It should start with `postgresql://` and be marked as **System**

---

## 📊 **Step 5: Database Environment Management**

### **5.1 Environment-Specific Initialization**
The app automatically detects the environment:

```python
# In backend/database.py
def get_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not configured")
    
    # Automatically uses the correct database based on environment
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
```

### **5.2 Migration Between Environments**
To copy data from development to production:

```bash
# Export development data
pg_dump $DEV_DATABASE_URL > dev_backup.sql

# Import to production (be careful!)
psql $PROD_DATABASE_URL < dev_backup.sql
```

---

## 🔍 **Step 6: Verification**

### **6.1 Test Development Environment**
```bash
# Start local development server
FLASK_ENV=development python3 backend/app.py

# Check database status
curl http://localhost:5000/api/db-status
```

### **6.2 Test Production Environment**
```bash
# Deploy to production
git add .
git commit -m "Add PostgreSQL environment setup"
git push

# Check production database status
curl https://your-app.vercel.app/api/db-status
```

---

## 🛡️ **Best Practices**

### **🔐 Security**
- **Never commit** `.env.local` or `.env.production` files
- Use **different SECRET_KEY** values for each environment  
- Set **strong passwords** for database users
- Use **environment-specific domains** for CORS

### **📋 Data Management**
- Keep **development data** separate from production
- Use **database migrations** for schema changes
- **Backup production** data regularly
- **Test migrations** in development first

### **🚀 Deployment**
- Use **Vercel's automatic deployments** from Git
- Set **environment variables** in Vercel dashboard
- **Monitor database** performance and usage
- Set up **alerts** for database errors

---

## 📁 **Environment Files Structure**

```bash
sloka3.0/scwa/
├── .env.local          # Local development (not in Git)
├── .env.production     # Production reference (not in Git)
├── .env.example        # Template for both environments
└── backend/
    ├── database.py     # Handles both environments automatically
    └── app.py          # Detects environment via FLASK_ENV
```

---

## 🆘 **Troubleshooting**

### **Connection Issues**
```bash
# Test database connectivity
python3 -c "
import os, psycopg2
url = os.environ.get('DATABASE_URL')
if url:
    try:
        conn = psycopg2.connect(url)
        print('✅ Connected successfully!')
        conn.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')
else:
    print('❌ DATABASE_URL not set')
"
```

### **Environment Detection**
```bash
# Check current environment
python3 -c "
import os
env = os.environ.get('FLASK_ENV', 'development')
db_url = os.environ.get('DATABASE_URL', 'Not set')
print(f'Environment: {env}')
print(f'Database: {db_url[:30]}...' if db_url != 'Not set' else 'Database: Not configured')
"
```

---

## ✅ **Verification Checklist**

- [ ] Development PostgreSQL database created in Vercel
- [ ] Production PostgreSQL database created in Vercel
- [ ] `.env.local` configured with development DATABASE_URL
- [ ] Production environment variables set in Vercel
- [ ] Local development server connects successfully
- [ ] Production deployment connects successfully
- [ ] Database initialization works in both environments
- [ ] Admin login works in both environments

**🎉 You now have two separate PostgreSQL environments ready for development and production!**
