import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { getSession, clearSession } from '../auth'

export default function AdminLayout({ children }) {
  const session = getSession()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    clearSession()
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top navbar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <img src="/lotus.svg" alt="Sai Kalpataru" />
          Sai Kalpataru Admin
        </div>
        <button
          className="navbar-hamburger"
          onClick={() => setMenuOpen(v => !v)}
          aria-label="Toggle menu"
        >
          {menuOpen ? '✕' : '☰'}
        </button>
        <div className={`navbar-nav${menuOpen ? ' open' : ''}`}>
          <span className="nav-user">🕉 {session?.username}</span>
          <span className="badge badge-admin">Admin</span>
          <button className="btn btn-secondary btn-sm" onClick={handleLogout} style={{ marginLeft: '8px' }}>
            Logout
          </button>
        </div>
      </nav>

      {/* Body: sidebar + content */}
      <div className="admin-layout" style={{ flex: 1 }}>
        <aside className="admin-sidebar">
          <div className="sidebar-label">Courses</div>
          <NavLink
            to="/admin"
            end
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            📚 All Courses
          </NavLink>
          <NavLink
            to="/admin/courses/new"
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            ➕ New Course
          </NavLink>

          <div className="sidebar-label" style={{ marginTop: '16px' }}>Students</div>
          <NavLink
            to="/admin/students"
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            👥 Manage Students
          </NavLink>

          <div className="sidebar-label" style={{ marginTop: '16px' }}>Portal</div>
          <NavLink
            to="/admin/settings"
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            ⚙️ Settings
          </NavLink>
        </aside>

        <main className="admin-main">
          {children}
        </main>
      </div>
    </div>
  )
}
