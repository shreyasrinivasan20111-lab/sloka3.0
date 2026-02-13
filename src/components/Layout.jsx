import { NavLink, useNavigate } from 'react-router-dom'
import { getSession, clearSession } from '../auth'

export default function Layout({ children }) {
  const session = getSession()
  const navigate = useNavigate()

  function handleLogout() {
    clearSession()
    navigate('/login')
  }

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <img src="/lotus.svg" alt="Sai Kalpataru" />
          Sai Kalpataru
        </div>
        <div className="navbar-nav">
          {session?.role === 'admin' && (
            <>
              <NavLink to="/admin" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} end>
                Dashboard
              </NavLink>
              <NavLink to="/admin/courses/new" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                + Course
              </NavLink>
              <NavLink to="/admin/students" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                Students
              </NavLink>
              <NavLink to="/admin/settings" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                Settings
              </NavLink>
            </>
          )}
          {session?.role === 'student' && (
            <NavLink to="/student" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
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
