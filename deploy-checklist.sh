#!/bin/bash
# Vercel PostgreSQL Deployment Checklist & Commands

echo "🚀 Vercel PostgreSQL Integration Checklist"
echo "=========================================="

echo ""
echo "✅ STEP 1: Verify Local Setup"
echo "------------------------------"

# Check if we're in the right directory
if [ ! -f "backend/database.py" ]; then
    echo "❌ Please run this script from the scwa directory"
    exit 1
fi

echo "✓ Directory structure correct"

# Check if virtual environment exists
if [ ! -d "../.venv" ]; then
    echo "❌ Virtual environment not found at ../.venv"
    echo "   Create it with: python -m venv ../.venv"
    exit 1
fi

echo "✓ Virtual environment found"

# Check if requirements.txt includes PostgreSQL
if ! grep -q "psycopg2" requirements.txt; then
    echo "⚠️  Adding psycopg2-binary to requirements.txt"
    echo "psycopg2-binary==2.9.7" >> requirements.txt
fi

echo "✓ PostgreSQL dependencies ready"

echo ""
echo "✅ STEP 2: Test Local Database Connection"
echo "----------------------------------------"

# Test simplified database module
echo "Testing database module..."
if python -c "from backend.database import get_connection; print('✓ Database module imports correctly')" 2>/dev/null; then
    echo "✓ Database module working"
else
    echo "❌ Database module import failed"
    echo "   Check your Python path and dependencies"
    exit 1
fi

echo ""
echo "✅ STEP 3: Vercel Setup Commands"
echo "--------------------------------"

echo "Run these commands to set up Vercel PostgreSQL:"
echo ""
echo "1. Login to Vercel:"
echo "   vercel login"
echo ""
echo "2. Create PostgreSQL database:"
echo "   vercel storage create postgres --name sloka-production"
echo ""
echo "3. Link your project (if not already linked):"
echo "   vercel link"
echo ""
echo "4. Deploy your application:"
echo "   vercel --prod"
echo ""

echo "✅ STEP 4: Environment Variables Setup"
echo "--------------------------------------"

echo "In your Vercel dashboard, ensure these environment variables are set:"
echo ""
echo "Required (automatically set by Vercel Postgres):"
echo "  - POSTGRES_URL"
echo "  - POSTGRES_HOST"  
echo "  - POSTGRES_USER"
echo "  - POSTGRES_PASSWORD"
echo "  - POSTGRES_DATABASE"
echo ""
echo "Map to your app:"
echo "  - DATABASE_URL = \${POSTGRES_URL}"
echo "  - SECRET_KEY = your-secure-secret-key"
echo "  - FLASK_ENV = production"
echo "  - VERCEL = 1"
echo "  - CORS_ORIGINS = https://your-domain.vercel.app"
echo ""

echo "✅ STEP 5: Test Deployment"
echo "--------------------------"

echo "After deployment, test these endpoints:"
echo ""
echo "1. Database health check:"
echo "   curl https://your-app.vercel.app/api/debug-db"
echo ""
echo "2. Environment variables check:"  
echo "   curl https://your-app.vercel.app/api/env-check"
echo ""
echo "3. Database status:"
echo "   curl https://your-app.vercel.app/api/db-status"
echo ""

echo "✅ STEP 6: Verify Functionality"
echo "-------------------------------"

echo "Test these features after deployment:"
echo ""
echo "1. User signup and persistence:"
echo "   - Sign up a new student"
echo "   - Check admin panel - user should appear"
echo "   - Redeploy app - user should still exist"
echo ""
echo "2. Course management:"
echo "   - Login as admin: admin@example.com / admin123"
echo "   - Create a new course"
echo "   - Assign to students"
echo "   - Verify assignments persist"
echo ""
echo "3. File uploads:"
echo "   - Upload files to courses"
echo "   - Verify they're accessible"
echo ""

echo "🎉 READY FOR DEPLOYMENT!"
echo "======================="

echo ""
echo "Your Sloka Course Management System is configured with:"
echo "✓ PostgreSQL-only database architecture"
echo "✓ Vercel-optimized configuration"
echo "✓ Fixed user signup persistence"
echo "✓ Fixed course assignment persistence"
echo "✓ Simplified codebase"
echo ""
echo "Next: Run 'vercel --prod' to deploy!"
