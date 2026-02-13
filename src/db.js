import { createClient } from '@libsql/client/http'

let _client = null

export function getClient() {
  if (!_client) {
    _client = createClient({
      url: import.meta.env.VITE_TURSO_DATABASE_URL,
      authToken: import.meta.env.VITE_TURSO_AUTH_TOKEN,
    })
  }
  return _client
}

export async function initDB() {
  const db = getClient()

  await db.execute(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'student',
      created_at TEXT DEFAULT (datetime('now'))
    )
  `)

  await db.execute(`
    CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      content TEXT,
      created_by INTEGER,
      created_at TEXT DEFAULT (datetime('now'))
    )
  `)

  await db.execute(`
    CREATE TABLE IF NOT EXISTS attachments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      course_id INTEGER NOT NULL,
      label TEXT NOT NULL,
      url TEXT NOT NULL,
      file_type TEXT NOT NULL,
      FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    )
  `)

  await db.execute(`
    CREATE TABLE IF NOT EXISTS course_assignments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      course_id INTEGER NOT NULL,
      student_id INTEGER NOT NULL,
      UNIQUE(course_id, student_id),
      FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
      FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
    )
  `)

  await db.execute(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    )
  `)

  // Seed default settings
  await db.execute(`
    INSERT OR IGNORE INTO settings (key, value) VALUES ('portal_closed', 'false')
  `)
  await db.execute(`
    INSERT OR IGNORE INTO settings (key, value) VALUES ('chat_enabled', 'false')
  `)

  // Seed default admin
  await db.execute(`
    INSERT OR IGNORE INTO users (username, email, password, role)
    VALUES ('admin', 'admin@saikalpataru.app', 'admin123', 'admin')
  `)
}

// ─── Users ────────────────────────────────────────────────────────────────────

export async function getUserByLogin(identifier, password) {
  const db = getClient()
  const result = await db.execute({
    sql: `SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ? LIMIT 1`,
    args: [identifier, identifier, password],
  })
  return result.rows[0] || null
}

export async function getAllStudents() {
  const db = getClient()
  const result = await db.execute(`SELECT * FROM users WHERE role = 'student' ORDER BY username`)
  return result.rows
}

export async function createStudent(username, email, password) {
  const db = getClient()
  await db.execute({
    sql: `INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'student')`,
    args: [username, email, password],
  })
}

export async function deleteStudent(id) {
  const db = getClient()
  await db.execute({ sql: `DELETE FROM users WHERE id = ? AND role = 'student'`, args: [id] })
}

export async function updateStudentPassword(id, password) {
  const db = getClient()
  await db.execute({ sql: `UPDATE users SET password = ? WHERE id = ?`, args: [password, id] })
}

// ─── Courses ──────────────────────────────────────────────────────────────────

export async function getAllCourses() {
  const db = getClient()
  const result = await db.execute(`SELECT * FROM courses ORDER BY created_at DESC`)
  return result.rows
}

export async function getCourseById(id) {
  const db = getClient()
  const result = await db.execute({ sql: `SELECT * FROM courses WHERE id = ?`, args: [id] })
  return result.rows[0] || null
}

export async function createCourse(title, description, content, createdBy) {
  const db = getClient()
  const result = await db.execute({
    sql: `INSERT INTO courses (title, description, content, created_by) VALUES (?, ?, ?, ?)`,
    args: [title, description, content, createdBy],
  })
  return result.lastInsertRowid
}

export async function updateCourse(id, title, description, content) {
  const db = getClient()
  await db.execute({
    sql: `UPDATE courses SET title = ?, description = ?, content = ? WHERE id = ?`,
    args: [title, description, content, id],
  })
}

export async function deleteCourse(id) {
  const db = getClient()
  await db.execute({ sql: `DELETE FROM courses WHERE id = ?`, args: [id] })
}

// ─── Attachments ──────────────────────────────────────────────────────────────

export async function getAttachmentsByCourse(courseId) {
  const db = getClient()
  const result = await db.execute({
    sql: `SELECT * FROM attachments WHERE course_id = ? ORDER BY id`,
    args: [courseId],
  })
  return result.rows
}

export async function addAttachment(courseId, label, url, fileType) {
  const db = getClient()
  await db.execute({
    sql: `INSERT INTO attachments (course_id, label, url, file_type) VALUES (?, ?, ?, ?)`,
    args: [courseId, label, url, fileType],
  })
}

export async function deleteAttachment(id) {
  const db = getClient()
  await db.execute({ sql: `DELETE FROM attachments WHERE id = ?`, args: [id] })
}

// ─── Course Assignments ───────────────────────────────────────────────────────

export async function getAssignedStudents(courseId) {
  const db = getClient()
  const result = await db.execute({
    sql: `SELECT u.* FROM users u
          JOIN course_assignments ca ON ca.student_id = u.id
          WHERE ca.course_id = ?`,
    args: [courseId],
  })
  return result.rows
}

export async function getAssignedCourses(studentId) {
  const db = getClient()
  const result = await db.execute({
    sql: `SELECT c.* FROM courses c
          JOIN course_assignments ca ON ca.course_id = c.id
          WHERE ca.student_id = ?
          ORDER BY c.created_at DESC`,
    args: [studentId],
  })
  return result.rows
}

export async function assignCourse(courseId, studentId) {
  const db = getClient()
  await db.execute({
    sql: `INSERT OR IGNORE INTO course_assignments (course_id, student_id) VALUES (?, ?)`,
    args: [courseId, studentId],
  })
}

export async function unassignCourse(courseId, studentId) {
  const db = getClient()
  await db.execute({
    sql: `DELETE FROM course_assignments WHERE course_id = ? AND student_id = ?`,
    args: [courseId, studentId],
  })
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export async function getSetting(key) {
  const db = getClient()
  const result = await db.execute({
    sql: `SELECT value FROM settings WHERE key = ?`,
    args: [key],
  })
  return result.rows[0]?.value ?? null
}

export async function setSetting(key, value) {
  const db = getClient()
  await db.execute({
    sql: `INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)`,
    args: [key, value],
  })
}

export async function getAllSettings() {
  const db = getClient()
  const result = await db.execute(`SELECT * FROM settings`)
  const map = {}
  for (const row of result.rows) {
    map[row.key] = row.value
  }
  return map
}
