import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { initDB } from './db'

import HomePage from './pages/HomePage'
import Login from './pages/Login'
import StudentSignup from './pages/StudentSignup'
import StudentDashboard from './pages/StudentDashboard'
import CourseView from './pages/CourseView'
import AdminDashboard from './pages/admin/AdminDashboard'
import CourseForm from './pages/admin/CourseForm'
import StudentManagement from './pages/admin/StudentManagement'
import AttendanceManagement from './pages/admin/AttendanceManagement'
import Settings from './pages/admin/Settings'
import ProtectedRoute from './components/ProtectedRoute'


export default function App() {
  const [dbReady, setDbReady] = useState(false)
  const [dbError, setDbError] = useState('')

  useEffect(() => {
    initDB()
      .then(() => setDbReady(true))
      .catch(err => {
        console.error('DB init failed:', err)
        setDbError('Could not connect to the database. Please check your connection.')
        setDbReady(true) // Still render so user sees the error on login
      })
  }, [])

  if (!dbReady) {
    return (
      <div className="spinner-overlay">
        <div className="spinner" />
        <div className="spinner-text">Awakening the portal...</div>
      </div>
    )
  }

  if (dbError) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--cream)' }}>
        <div className="card" style={{ maxWidth: '420px', textAlign: 'center' }}>
          <img src="/lotus.svg" alt="" style={{ width: 60, marginBottom: 16 }} />
          <h2 style={{ marginBottom: 12 }}>Connection Error</h2>
          <div className="alert alert-error">{dbError}</div>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<StudentSignup />} />

        {/* Student routes */}
        <Route path="/student" element={
          <ProtectedRoute role="student"><StudentDashboard /></ProtectedRoute>
        } />
        <Route path="/student/course/:id" element={
          <ProtectedRoute><CourseView /></ProtectedRoute>
        } />

        {/* Admin routes */}
        <Route path="/admin" element={
          <ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>
        } />
        <Route path="/admin/courses/new" element={
          <ProtectedRoute role="admin"><CourseForm /></ProtectedRoute>
        } />
        <Route path="/admin/courses/:id/edit" element={
          <ProtectedRoute role="admin"><CourseForm /></ProtectedRoute>
        } />
        <Route path="/admin/students" element={
          <ProtectedRoute role="admin"><StudentManagement /></ProtectedRoute>
        } />
        <Route path="/admin/attendance" element={
          <ProtectedRoute role="admin"><AttendanceManagement /></ProtectedRoute>
        } />
        <Route path="/admin/settings" element={
          <ProtectedRoute role="admin"><Settings /></ProtectedRoute>
        } />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
