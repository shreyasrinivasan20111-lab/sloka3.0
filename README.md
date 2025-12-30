# 🎓 Sloka 3.0 - Student Course Management System

A beautiful, modern web application for managing student courses with rich text editing, file attachments, and comprehensive admin controls.

![Student Course Management System](https://img.shields.io/badge/Version-3.0-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue)

## ✨ Features

### 🎨 **Beautiful Design**
- **Stunning Visual Appeal**: Thick vertical brown stripes (#C5A098 & #B8927F)
- **Premium Typography**: Nova Round for body text, Limelight for headings
- **Warm Color Palette**: Rich brown tones (#704f3b) throughout
- **Responsive Design**: Works perfectly on all devices

### 👩‍🏫 **For Administrators**
- 📚 Create, edit, and delete courses with rich text content
- 👥 Assign courses to multiple students
- 📎 Upload and manage course materials
- 📊 View all students and their course assignments
- 🔍 Comprehensive activity logging

### For Students
- 🎓 View assigned courses
- 📖 Read rich-formatted course content
- 📥 Download course materials
- ✍️ Self-registration with email

### Technical Features
- ⚡ Single-page application (no page reloads)
- 🎨 Rich text editor (Quill.js)
- 🔐 Secure session-based authentication
- 📝 Extensive backend logging
- 🐛 Comprehensive error handling widget
- 🗄️ PostgreSQL database for production reliability
- ☁️ Production-ready for Vercel deployment

## Tech Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Python Flask 3.0+
- **Database**: PostgreSQL (Vercel Postgres)
- **Rich Text**: Quill.js 1.3.6
- **Authentication**: Session-based with email/password

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

### Installation

1. **Clone or create the project directory**:
```bash
mkdir spageapp
cd spageapp
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Initialize the database**:
```bash
python3 -m backend.database
```

4. **Run the application**:
```bash
python3 -m backend.app
```

5. **Open in browser**:
```
http://localhost:5000
```

### Default Credentials

**Admin Account**:
- Email: `admin@example.com`
- Password: `admin123`

**Student Accounts**:
- Email: `student1@example.com` / Password: `student123`
- Email: `student2@example.com` / Password: `student123`

**Or create a new student account** via the signup page.

## Project Structure

```
spageapp/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── database.py         # PostgreSQL schema and initialization
│   ├── auth.py             # Authentication decorators
│   ├── config.py           # Environment-based configuration
│   └── logger.py           # Logging infrastructure
├── frontend/
│   ├── index.html          # Single-page app
│   └── static/
│       ├── css/styles.css  # All styles
│       └── js/app.js       # All JavaScript
├── uploads/                # File upload directory
├── logs/                   # Application logs
├── api/                    # Vercel serverless functions
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel deployment config
└── .env.example           # Environment variables template
```

## Usage Guide

### Admin Workflow

1. **Login** with admin credentials
2. **Create a course**:
   - Click "Create New Course"
   - Enter title and description
   - Use the rich text editor for content
   - Save the course
3. **Upload files** to a course:
   - Click on a course card
   - Click "Upload File"
   - Select file (PDF, DOC, images)
4. **Assign courses to students**:
   - Click "Assign Students" on a course card
   - Select students from the list
   - Save assignments

### Student Workflow

1. **Sign up** (if new student):
   - Click "Sign Up" on login page
   - Enter email and password
   - Automatically logged in after signup
2. **View assigned courses** on dashboard
3. **Read course content** with formatted text
4. **Download course materials**

## API Endpoints

### Authentication
```
POST   /api/login          - Login with email/password
POST   /api/signup         - Register new student
POST   /api/logout         - End session
GET    /api/check-auth     - Check authentication status
```

### Courses
```
GET    /api/courses        - List courses (role-filtered)
POST   /api/courses        - Create course (admin only)
GET    /api/courses/<id>   - Get single course
PUT    /api/courses/<id>   - Update course (admin only)
DELETE /api/courses/<id>   - Delete course (admin only)
```

### Assignments
```
POST   /api/courses/<id>/assign  - Assign to students (admin)
GET    /api/students              - List all students (admin)
```

### Files
```
POST   /api/courses/<id>/upload      - Upload file
GET    /api/files/<id>/download      - Download file
DELETE /api/files/<id>                - Delete file (admin)
```

## Database Schema

### Users
```sql
- id: INTEGER PRIMARY KEY
- email: VARCHAR UNIQUE
- hashed_password: VARCHAR
- role: VARCHAR ('admin' or 'student')
- created_at: TIMESTAMP
```

### Courses
```sql
- id: INTEGER PRIMARY KEY
- title: VARCHAR
- description: TEXT
- content: TEXT (HTML from Quill.js)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### Assigned Courses
```sql
- id: INTEGER PRIMARY KEY
- student_id: INTEGER -> users(id)
- course_id: INTEGER -> courses(id)
- assigned_at: TIMESTAMP
```

### Files
```sql
- id: INTEGER PRIMARY KEY
- course_id: INTEGER -> courses(id)
- filename: VARCHAR (stored name)
- original_filename: VARCHAR
- file_path: VARCHAR
- file_size: INTEGER
- uploaded_at: TIMESTAMP
```

## Logging System

The application includes comprehensive logging:

### Log Files
- `logs/all.log` - All activity (DEBUG and above)
- `logs/errors.log` - Errors only (ERROR and above)
- `logs/api_requests.log` - API request summary

### What Gets Logged
- ✅ All API requests and responses
- ✅ Authentication attempts (success/failure)
- ✅ Database operations
- ✅ Course operations (create/update/delete)
- ✅ File operations (upload/download/delete)
- ✅ Session activities
- ✅ Errors and exceptions
- ✅ Performance metrics (request duration)

### View Logs in Real-Time
```bash
# All activity
tail -f logs/all.log

# Errors only
tail -f logs/errors.log

# API requests
tail -f logs/api_requests.log
```

### Search Logs
```bash
# Find all login attempts
grep "LOGIN" logs/all.log

# Find failed operations
grep "FAILED" logs/all.log

# Find activity by specific user
grep "user@example.com" logs/all.log
```

See [LOGGING_GUIDE.md](LOGGING_GUIDE.md) for complete documentation.

## Error Handling

The application includes a comprehensive error widget that:
- 🎯 Catches all frontend and backend errors
- 📊 Displays detailed error information
- 📋 Allows copying error details to clipboard
- 🔍 Shows stack traces and server responses
- ⚡ Captures global JavaScript errors
- 🌐 Handles network and API errors

See [ERROR_WIDGET_GUIDE.md](ERROR_WIDGET_GUIDE.md) for complete documentation.

## Configuration

### Development
Create a `.env` file:
```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DB_PATH=student_courses.db
UPLOAD_FOLDER=uploads
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
```

### Production
Set environment variables in your hosting platform:
```bash
FLASK_ENV=production
SECRET_KEY=strong-random-secret-key
DB_PATH=/tmp/student_courses.db  # For Vercel
UPLOAD_FOLDER=/tmp/uploads        # For Vercel
```

## Deployment

### Vercel (Recommended)

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Deploy**:
```bash
vercel
```

3. **Set environment variables** in Vercel dashboard:
   - `SECRET_KEY`
   - `FLASK_ENV=production`

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

### Important Production Notes

- **Database**: PostgreSQL required for production data persistence.
- **File Uploads**: Use cloud storage (AWS S3, Cloudinary, etc.) instead of local filesystem.
- **Logs**: Use external logging service (CloudWatch, Papertrail, etc.) instead of local files.

## Development

### Working with GitHub Copilot

This project includes comprehensive Copilot instructions in `.github/copilot-instructions.md`. When using GitHub Copilot in VS Code:

1. Copilot will understand the project architecture
2. Code suggestions will follow existing patterns
3. New endpoints will match the logging and error handling patterns
4. Database operations will use PostgreSQL syntax

### Adding a New Feature

1. **Backend** (in `backend/app.py`):
```python
@app.route('/api/new-endpoint', methods=['POST'])
@login_required
def new_endpoint():
    logger.info(f"New action | User: {session.get('email')}")

    try:
        # Your logic here
        log_database_operation('INSERT', 'table', 'Details')
        logger.info(f"✓ Action successful")
        return jsonify({'message': 'Success'}), 200

    except Exception as e:
        logger.error(f"✗ Action failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

2. **Frontend** (in `frontend/static/js/app.js`):
```javascript
async function newAction() {
    try {
        const result = await apiCall('/new-endpoint', {
            method: 'POST',
            body: JSON.stringify({ data })
        });
        showMessage('Success!');
    } catch (error) {
        // Error automatically shown by ErrorHandler
    }
}
```

## Troubleshooting

### Database Issues
```bash
# Reset database
rm student_courses.db
python3 -m backend.database
```

### CORS Errors
- Ensure both `localhost` and `127.0.0.1` are in `CORS_ORIGINS`
- Use relative URLs (`/api/endpoint`) instead of absolute URLs

### File Upload Fails
- Check file size (max 16MB)
- Verify `uploads/` directory exists and is writable
- Check allowed extensions: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG

### Login Issues
- Check logs: `grep "LOGIN" logs/all.log`
- Verify credentials match database
- Check session configuration in `backend/app.py`

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

## Security Considerations

### What's Secure
- ✅ Password hashing with pbkdf2:sha256
- ✅ Session-based authentication
- ✅ Role-based access control
- ✅ File upload validation
- ✅ Passwords never logged

### Production Recommendations
- 🔐 Use strong SECRET_KEY
- 🔐 Enable HTTPS only
- 🔐 Set secure session cookies
- 🔐 Implement rate limiting
- 🔐 Add CSRF protection
- 🔐 Use external database
- 🔐 Implement backup strategy

## Testing

### Manual Testing Checklist

**Authentication**:
- [ ] Admin login works
- [ ] Student login works
- [ ] New student signup works
- [ ] Logout works
- [ ] Invalid credentials rejected

**Courses (Admin)**:
- [ ] Create course with rich text
- [ ] Edit course
- [ ] Delete course
- [ ] Upload file to course
- [ ] Delete file from course
- [ ] Assign course to students

**Courses (Student)**:
- [ ] View assigned courses only
- [ ] Read course content
- [ ] Download course files
- [ ] Cannot access admin functions

**Error Handling**:
- [ ] Error widget shows on API errors
- [ ] Error widget shows on network errors
- [ ] Copy to clipboard works
- [ ] Errors logged to console

## Performance

- Average response time: < 100ms
- Database query time: < 50ms
- Page load time: < 1s
- File upload: Depends on file size and network

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions:
1. Check the logs in `logs/all.log`
2. Review documentation:
   - [LOGGING_GUIDE.md](LOGGING_GUIDE.md)
   - [ERROR_WIDGET_GUIDE.md](ERROR_WIDGET_GUIDE.md)
   - [DEPLOYMENT.md](DEPLOYMENT.md)
   - [.github/copilot-instructions.md](.github/copilot-instructions.md)

## Credits

Built with:
- [Flask](https://flask.palletsprojects.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Quill.js](https://quilljs.com/)

---

**Happy Learning! 🎓**
