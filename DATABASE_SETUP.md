# 🗄️ External Database Setup Guide

## Problem: Data Loss in Serverless Deployments

Your current issue is that **every Vercel deployment resets the database**, deleting all your courses and student data. This happens because Vercel's serverless environment has ephemeral storage.

## 🎯 Solution: External PostgreSQL Database

By switching to an external PostgreSQL database, your data will persist forever, even through deployments.

## 📋 Quick Setup Options

### Option 1: Supabase (Recommended - Free Tier)

1. **Create Account**: Go to [supabase.com](https://supabase.com) and sign up
2. **New Project**: Click "New Project" and choose a name
3. **Get Connection**: Go to Settings → Database → Connection String
4. **Copy URL**: Copy the connection string (looks like `postgresql://...`)

### Option 2: Neon (Serverless PostgreSQL)

1. **Create Account**: Go to [neon.tech](https://neon.tech) and sign up  
2. **New Database**: Create a new database
3. **Get Connection**: Copy the connection string from dashboard

### Option 3: PlanetScale (MySQL Alternative)

1. **Create Account**: Go to [planetscale.com](https://planetscale.com)
2. **New Database**: Create a new database
3. **Get Connection**: Copy connection details

## 🚀 Implementation Steps

### Step 1: Get Your Database URL

After setting up with Supabase (or other provider), you'll have a connection string like:
```
postgresql://postgres:your-password@db.abc123.supabase.co:5432/postgres
```

### Step 2: Configure for Local Development

Create a `.env` file in your project root:
```bash
# Add this line to your .env file
DATABASE_URL=your-connection-string-here
```

### Step 3: Configure for Vercel Deployment

1. Go to your Vercel dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add new variable:
   - **Name**: `DATABASE_URL`
   - **Value**: Your connection string
   - **Environments**: Production, Preview, Development

### Step 4: Migrate Your Existing Data

Run the setup script to migrate your current courses:
```bash
python setup_database.py
# Choose PostgreSQL setup for production deployment
```

### Step 5: Deploy

```bash
git add .
git commit -m "Add PostgreSQL database support"
git push
```

## 🎉 Results

✅ **Your courses will persist forever**  
✅ **No more data loss on deployments**  
✅ **Better performance and reliability**  
✅ **Scales with your user base**  

## 🔧 Technical Details

The system automatically detects your database configuration:

- **Production**: Uses PostgreSQL via DATABASE_URL environment variable
- **Production**: Uses PostgreSQL when `DATABASE_URL` is configured
- **Migration**: Seamless migration script preserves all your data

## 💡 Why These Providers?

- **Supabase**: Full PostgreSQL with 500MB free, excellent documentation
- **Neon**: Serverless PostgreSQL with branching, great for developers  
- **PlanetScale**: MySQL-based but with excellent Vercel integration

## 🆘 Troubleshooting

**Connection Issues**: Check your connection string format and credentials

**Migration Problems**: Ensure your local database has data before migrating

**Vercel Deployment**: Make sure `DATABASE_URL` is set in Vercel environment variables

**Dependencies**: The system will automatically install `psycopg2-binary` for PostgreSQL support

## 📞 Need Help?

1. Run `python setup_database.py` and choose option 1 to check your configuration
2. Check the logs for specific error messages
3. Verify your `DATABASE_URL` format matches the provider's documentation

Your data persistence problem will be completely solved! 🎯
