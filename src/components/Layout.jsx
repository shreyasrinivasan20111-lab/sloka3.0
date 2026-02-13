import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { getSession, clearSession } from '../auth'

export default function Layout({ children }) {
  const session = getSession()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    clearSession()
    navigate('/login')
  }

  function closeMenu() {
    setMenuOpen(false)
  }

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <img src="/lotus.svg" alt="Sai Kalpataru" />
          Sai Kalpataru
        </div>
        <button
          className="navbar-hamburger"
          onClick={() => setMenuOpen(v => !v)}
          aria-label="Toggle menu"
        >
          {menuOpen ? '✕' : '☰'}
        </button>
        <div className={`navbar-nav${menuOpen ? ' open' : ''}`}>
          {session?.role === 'admin' && (
            <>
              <NavLink to="/admin" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} end onClick={closeMenu}>
                Dashboard
              </NavLink>
              <NavLink to="/admin/courses/new" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={closeMenu}>
                + Course
              </NavLink>
              <NavLink to="/admin/students" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={closeMenu}>
                Students
              </NavLink>
              <NavLink to="/admin/settings" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={closeMenu}>
                Settings
              </NavLink>
            </>
          )}
          {session?.role === 'student' && (
            <NavLink to="/student" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={closeMenu}>
              My Courses
            </NavLink>
          )}
          {session && (
            <>
              <span className="nav-user">
                {session.role === 'admin' ? '🕉' : '🙏'} {session.username}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                Logout
              </button>
            </>
          )}
        </div>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
