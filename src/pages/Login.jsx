import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUserByLogin } from '../db'
import { setSession, getSession } from '../auth'
import { getSetting } from '../db'

export default function Login() {
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Already logged in
  const session = getSession()
  if (session) {
    navigate(session.role === 'admin' ? '/admin' : '/student', { replace: true })
    return null
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      // Check portal closed (only blocks students)
      const portalClosed = await getSetting('portal_closed')
      if (portalClosed === 'true') {
        // We need to know role before blocking — get user first
        const user = await getUserByLogin(identifier.trim(), password)
        if (!user) {
          setError('Invalid username/email or password.')
          return
        }
        if (user.role === 'student') {
          setError('The portal is currently closed. Please contact your administrator.')
          return
        }
        setSession(user)
        navigate('/admin')
        return
      }

      const user = await getUserByLogin(identifier.trim(), password)
      if (!user) {
        setError('Invalid username/email or password.')
        return
      }
      setSession(user)
      navigate(user.role === 'admin' ? '/admin' : '/student')
    } catch (err) {
      setError('Connection error. Please check your internet and try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <img src="/lotus.svg" alt="Sai Kalpataru" />
          <h1>Sai Kalpataru</h1>
          <p>Sacred Learning Portal</p>
        </div>

        <div className="divider">
          <span>✦</span>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="identifier">Username or Email</label>
            <input
              id="identifier"
              className="form-control"
              type="text"
              value={identifier}
              onChange={e => setIdentifier(e.target.value)}
              placeholder="Enter username or email"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              className="form-control"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? 'Entering...' : '🕉 Enter the Portal'}
          </button>
        </form>

        <div className="lotus-ornament" style={{ marginTop: '28px' }}>
          <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem', letterSpacing: '0.08em' }}>
            ॐ तत् सत् — That which is truth
          </small>
        </div>
      </div>
    </div>
  )
}
