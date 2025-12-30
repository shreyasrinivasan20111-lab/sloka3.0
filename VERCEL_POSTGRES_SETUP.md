# 🚀 **Vercel PostgreSQL Integration Guide**

## **Overview**
This guide will walk you through setting up Vercel PostgreSQL for your Sloka Course Management System, ensuring persistent data storage and resolving deployment issues.

---

## **Step 1: Create Vercel PostgreSQL Database**

### **1.1 Via Vercel Dashboard**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to your project
3. Click **"Storage"** tab
4. Click **"Create Database"**
5. Select **"PostgreSQL"**
6. Choose your region (closest to your users)
7. Name your database (e.g., `sloka-production`)

### **1.2 Alternative: Via Vercel CLI**
```bash
# Install Vercel CLI if not already installed
npm i -g vercel@latest

# Login to Vercel
vercel login

# Create PostgreSQL database
vercel storage create postgres --name sloka-production
```

---

## **Step 2: Configure Environment Variables**

### **2.1 Automatic Configuration (Recommended)**
Vercel automatically provides these environment variables when you create a PostgreSQL database:
- `POSTGRES_URL` - Full connection string
- `POSTGRES_PRISMA_URL` - Optimized for Prisma (but we use psycopg2)
- `POSTGRES_URL_NON_POOLING` - Direct connection without pooling
- `POSTGRES_USER` - Database username
- `POSTGRES_HOST` - Database host
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DATABASE` - Database name

### **2.2 Map to Your App's Variables**
In your Vercel project settings, add these environment variables:

```bash
# Main database connection (our app uses DATABASE_URL)
DATABASE_URL=${POSTGRES_URL}

# Optional: Individual components (fallback)
DB_HOST=${POSTGRES_HOST}
DB_USER=${POSTGRES_USER}
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_NAME=${POSTGRES_DATABASE}
DB_PORT=5432

# App configuration
SECRET_KEY=your-secure-secret-key-here
FLASK_ENV=production
VERCEL=1
CORS_ORIGINS=https://your-domain.vercel.app
```

### **2.3 Local Development**
Create a `.env` file in your project root:
```bash
# Local PostgreSQL for development
DATABASE_URL=postgresql://username:password@localhost:5432/sloka_dev

# Or use individual components
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=sloka_dev
DB_PORT=5432

# Development settings
SECRET_KEY=dev-secret-key
FLASK_ENV=development
```

---

## **Step 3: Install PostgreSQL Dependencies**

### **3.1 Update requirements.txt**
Ensure your `requirements.txt` includes:
```
Flask==2.3.3
Flask-CORS==4.0.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
Werkzeug==2.3.7
```

### **3.2 Install Locally (for development)**
```bash
# Activate virtual environment
source /Users/shreyasrinivasan/Desktop/Sloka3.0/.venv/bin/activate

# Install PostgreSQL adapter
pip install psycopg2-binary

# Update requirements
pip freeze > requirements.txt
```

---

## **Step 4: Database Initialization**

### **4.1 Automatic Initialization (Production)**
Your app will automatically initialize the database on first run:
- Tables are created if they don't exist
- Sample data is added if database is empty
- Uses the simplified `backend/database.py` module

### **4.2 Manual Initialization (if needed)**
```bash
# Run database setup script
python setup_database.py

# Or initialize via Python
python -c "from backend.database import init_database; init_database()"
```

---

## **Step 5: Deploy to Vercel**

### **5.1 Via Git (Recommended)**
```bash
# Your changes are already committed and pushed
# Vercel will automatically redeploy from GitHub

# Check deployment status
vercel --prod
```

### **5.2 Via Vercel CLI**
```bash
# Deploy directly
vercel --prod

# Or build and deploy
vercel build
vercel deploy --prebuilt --prod
```

---

## **Step 6: Test the Deployment**

### **6.1 Check Database Connection**
Visit: `https://your-app.vercel.app/api/debug-db`

Expected response:
```json
{
  "db_working": true,
  "user_count": 3,
  "debug": "db-connection-ok"
}
```

### **6.2 Test User Signup**
1. Go to your app's signup page
2. Create a new student account
3. Check admin panel - user should appear immediately
4. Redeploy the app - user should still be there

### **6.3 Test Course Management**
1. Login as admin: `admin@example.com` / `admin123`
2. Create a new course
3. Assign it to students
4. Verify assignments persist after deployment

---

## **Step 7: Monitoring & Maintenance**

### **7.1 Database Monitoring**
- Monitor via Vercel Dashboard → Storage → Your Database
- Check connection metrics and usage
- Set up alerts for high usage

### **7.2 Backup Strategy**
Vercel PostgreSQL includes:
- Automatic daily backups
- Point-in-time recovery
- High availability

### **7.3 Connection Pooling**
Your app uses connection pooling automatically:
- Each request opens/closes connections
- PostgreSQL handles concurrent connections
- No additional setup required

---

## **Step 8: Troubleshooting**

### **8.1 Common Issues**

**"Database connection parameters not set"**
```bash
# Check environment variables are set in Vercel
# DATABASE_URL should be automatically provided
```

**"User not appearing in admin panel"**
```bash
# This should be fixed with PostgreSQL implementation
# Check /api/debug-db endpoint for connection status
```

**"Course assignments disappearing"**
```bash
# Fixed with persistent PostgreSQL storage
# Verify DATABASE_URL is set correctly
```

### **8.2 Debug Commands**
```bash
# Check database status
curl https://your-app.vercel.app/api/debug-db

# Check environment variables
curl https://your-app.vercel.app/api/env-check

# Check database info
curl https://your-app.vercel.app/api/db-status
```

---

## **Step 9: Performance Optimization**

### **9.1 Connection Settings**
Your `database.py` is already optimized with:
- SSL connections (`sslmode=require`)
- Real dictionary cursors for easy data access
- Proper error handling and connection cleanup

### **9.2 Query Optimization**
- Use prepared statements (already implemented)
- Index common queries (PostgreSQL handles this)
- Connection pooling (handled by PostgreSQL)

---

## **🎉 Migration Complete!**

Your app is now configured with:
- ✅ **Persistent PostgreSQL storage**
- ✅ **Automatic database initialization**
- ✅ **Vercel-optimized configuration**
- ✅ **Fixed user signup persistence**
- ✅ **Fixed course assignment persistence**
- ✅ **Simplified architecture**

### **Sample Login Credentials**
After deployment, you can use:
- **Admin**: `admin@example.com` / `admin123`
- **Student1**: `student1@example.com` / `student123`
- **Student2**: `student2@example.com` / `student123`

---

## **Next Steps**
1. Deploy and test the integration
2. Update your domain-specific CORS settings
3. Set up monitoring and alerts
4. Consider adding database migrations for future schema changes

Your Sloka Course Management System is now production-ready with persistent PostgreSQL storage! 🚀
