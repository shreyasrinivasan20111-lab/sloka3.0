# 🗄️ Persistent DuckDB Storage Setup Guide

This guide shows you how to store your DuckDB database file externally so it persists across deployments, **without needing PostgreSQL**.

## 🎯 **Quick Setup Options**

### **Option 1: Vercel Blob Storage (Recommended for Vercel)**

**1. Get Vercel Blob Token:**
```bash
# In your Vercel project dashboard
vercel env add BLOB_READ_WRITE_TOKEN
# Paste your token when prompted
```

**2. Set Environment Variables in Vercel:**
```bash
BLOB_READ_WRITE_TOKEN=vercel_blob_***your_token_here***
BLOB_NAME=student_courses.db
```

**3. Deploy - Data Will Persist Automatically! 🎉**

### **Option 2: Network Drive/Mounted Storage**

**1. Set Network Path:**
```bash
NETWORK_DB_PATH=/mnt/shared/student_courses.db
```

**2. Ensure the directory exists and is writable**

### **Option 3: AWS S3 Storage**

**1. Install dependencies:**
```bash
pip install boto3
```

**2. Set environment variables:**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=your-bucket-name
S3_KEY=student_courses.db
```

### **Option 4: Google Cloud Storage**

**1. Install dependencies:**
```bash
pip install google-cloud-storage
```

**2. Set environment variables:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET=your-bucket-name
GCS_BLOB=student_courses.db
```

---

## 📋 **How It Works**

### **Automatic Storage Detection**
The system automatically detects your storage configuration:

1. **Network Drive** - Checks `NETWORK_DB_PATH`
2. **Vercel Volume** - Checks `VERCEL_VOLUME_PATH`  
3. **Cloud Sync** - Checks for cloud storage tokens
4. **Local Fallback** - Uses regular local file

### **Sync Behavior**
- **Download**: On startup, downloads existing database from cloud
- **Auto-Upload**: After write operations, syncs to cloud in background
- **Manual Sync**: Admin can trigger sync via `/api/db-sync` endpoint

### **Storage Types Comparison**

| Storage Type | Persistence | Auto-Sync | Setup Difficulty | Cost |
|-------------|------------|-----------|------------------|------|
| **Vercel Blob** | ✅ Yes | ✅ Yes | 🟢 Easy | 💲 Low |
| **Network Drive** | ✅ Yes | ❌ No | 🟡 Medium | 💲 Free |
| **AWS S3** | ✅ Yes | ✅ Yes | 🟡 Medium | 💲 Low |
| **Google Cloud** | ✅ Yes | ✅ Yes | 🟡 Medium | 💲 Low |
| **Local File** | ❌ No* | ❌ No | 🟢 Easy | 💲 Free |

*Only persists in development, lost on serverless deployment

---

## 🚀 **Vercel Blob Setup (Detailed)**

### **Step 1: Enable Vercel Blob**
1. Go to your Vercel project dashboard
2. Navigate to **Storage** tab
3. Create a **Blob Store**
4. Copy the **Read/Write Token**

### **Step 2: Configure Environment**
In your Vercel project settings:

```bash
# Required
BLOB_READ_WRITE_TOKEN=vercel_blob_***your_token***

# Optional (uses defaults if not set)
BLOB_NAME=student_courses.db
BLOB_URL=https://your-project.vercel.app/api/blob/student_courses.db
```

### **Step 3: Deploy**
```bash
git add .
git commit -m "Add persistent DuckDB storage"
git push
```

**Your data will now persist across all deployments! 🎉**

---

## 🛠️ **Advanced Configuration**

### **Multiple Environment Support**
```bash
# Development
BLOB_NAME=student_courses_dev.db

# Staging  
BLOB_NAME=student_courses_staging.db

# Production
BLOB_NAME=student_courses_prod.db
```

### **Custom Network Storage**
```bash
# For systems with mounted network drives
NETWORK_DB_PATH=/mnt/nfs/databases/student_courses.db
NETWORK_DB_BACKUP=/mnt/backup/student_courses_backup.db
```

### **Hybrid Setup (PostgreSQL + DuckDB Backup)**
You can even use both - PostgreSQL for production and DuckDB as a backup:

```bash
# Primary database
DATABASE_URL=postgresql://...

# Backup storage  
BLOB_READ_WRITE_TOKEN=vercel_blob_***
BLOB_NAME=backup_student_courses.db
```

---

## 📊 **Monitoring & Management**

### **Check Storage Status**
Visit `/api/db-status` (admin only) to see:
- Storage type being used
- Database size and location
- Sync status
- Persistence confirmation

### **Manual Sync**
Trigger manual cloud sync via `/api/db-sync` (admin only)

### **Troubleshooting**

**Database not syncing?**
1. Check environment variables are set correctly
2. Verify cloud storage permissions
3. Check logs for sync errors
4. Try manual sync via API

**Performance concerns?**
- Cloud sync happens in background, doesn't block requests  
- Database downloads once on startup, not per request
- Local operations are still fast DuckDB performance

**Cost optimization:**
- Vercel Blob: Free tier includes 500MB
- AWS S3: $0.023/GB/month  
- GCS: Similar pricing to S3

---

## 🔍 **Comparison: External DuckDB vs PostgreSQL**

| Feature | External DuckDB | PostgreSQL |
|---------|----------------|------------|
| **Setup Time** | 5 minutes | 15-30 minutes |
| **Performance** | ⚡ Very Fast | 🟢 Fast |
| **Serverless Support** | ✅ Yes | ✅ Yes |
| **File Size Limit** | Cloud storage limits | None |
| **Concurrent Users** | Medium | High |
| **SQL Features** | DuckDB SQL | Full PostgreSQL |
| **Backup** | Automatic file copy | Requires setup |
| **Cost** | Storage only | Database + compute |

---

## ✅ **Quick Verification**

After setup, verify your configuration:

1. **Check Status**: Visit admin panel → Database Status
2. **Create Test Data**: Add a course
3. **Trigger Deployment**: Push a change to trigger redeploy  
4. **Verify Persistence**: Check if your test data survived

**If you see "✅ Data persists with external DuckDB storage" - you're all set! 🎉**

---

## 📞 **Support**

If you need help with setup:

1. Check the `/api/db-status` endpoint for detailed storage information
2. Look at server logs for sync errors
3. Verify your environment variables are correctly set
4. Test with a simple file upload to your chosen storage service

**This solution gives you PostgreSQL-level persistence with DuckDB simplicity! 🚀**
