import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { getUserByLogin, getSetting } from '../db'
import { setSession, getSession } from '../auth'

export default function HomePage() {
  const navigate = useNavigate()
  const session = getSession()

  const [showLogin, setShowLogin] = useState(false)
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (session) {
    return <Navigate to={session.role === 'admin' ? '/admin' : '/student'} replace />
  }

  function openLogin() {
    setError('')
    setIdentifier('')
    setPassword('')
    setShowLogin(true)
  }

  function closeLogin() {
    setShowLogin(false)
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const portalClosed = await getSetting('portal_closed')
      if (portalClosed === 'true') {
        const user = await getUserByLogin(identifier.trim(), password)
        if (!user) { setError('Invalid username/email or password.'); return }
        if (user.role === 'student') {
          setError('The portal is currently closed. Please contact your administrator.')
          return
        }
        setSession(user)
        navigate('/admin')
        return
      }
      const user = await getUserByLogin(identifier.trim(), password)
      if (!user) { setError('Invalid username/email or password.'); return }
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'linear-gradient(160deg, var(--cream) 0%, var(--cream-dark) 50%, #EEDED8 100%)' }}>

      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, var(--maroon), var(--maroon-dark))',
        padding: '0 32px',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 3px 16px rgba(92,0,0,0.4)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'Cinzel, serif', fontSize: '1.3rem', color: 'var(--gold-light)', letterSpacing: '0.06em' }}>
          <img src="/lotus.svg" alt="Sai Kalpataru" style={{ width: 36, height: 36 }} />
          Sai Kalpataru
        </div>
        <button className="btn btn-secondary btn-sm" onClick={openLogin} style={{ fontWeight: 700 }}>
          🕉 Login
        </button>
      </header>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '56px 24px 32px', position: 'relative' }}>
        <img src="/lotus.svg" alt="" style={{ width: 80, height: 80, opacity: 0.25, position: 'absolute', top: 24, left: '50%', transform: 'translateX(-50%)', pointerEvents: 'none' }} />
        <h1 style={{ fontFamily: 'Cinzel, serif', color: 'var(--maroon)', fontSize: 'clamp(1.6rem, 5vw, 2.6rem)', letterSpacing: '0.06em', marginBottom: '8px', position: 'relative' }}>
          Sai Kalpataru Vidyalaya
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '32px' }}>
          Sacred Learning Portal
        </p>
        <div className="divider"><span>✦</span></div>
      </div>

      {/* Mission Statement */}
      <main style={{ flex: 1, maxWidth: '780px', margin: '0 auto', padding: '0 24px 60px', width: '100%' }}>
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>🙏</span>
            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>About Us</h2>
          </div>
          <p style={{ color: 'var(--text-mid)', lineHeight: 1.8, marginBottom: '16px' }}>
            Sai Kalpataru Vidyalaya is a non-profit organization. It was formed in the year 2020, which began with teaching bhajans for young kids. Later, this evolved into a structured curriculum where shlokas from Vedic literature are taught throughout the academic year.
          </p>
          <p style={{ color: 'var(--text-mid)', lineHeight: 1.8 }}>
            The mission of this institution is to spread the word of Sanatana Dharma to the world and instill spiritual practice in young minds through recital of shlokas in Sanskrit language.
          </p>
        </div>

        <div className="card" style={{ marginBottom: '32px' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>📬</span>
            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Shloka Class Registration</h2>
          </div>
          <p style={{ color: 'var(--text-mid)', lineHeight: 1.8 }}>
            For more details on shloka class registration, please contact us at{' '}
            <a href="mailto:jayab2021@gmail.com" style={{ color: 'var(--saffron-dark)', fontWeight: 700 }}>
              jayab2021@gmail.com
            </a>
          </p>
        </div>

        <div style={{ textAlign: 'center' }}>
          <button className="btn btn-primary" onClick={openLogin} style={{ padding: '12px 36px', fontSize: '1rem' }}>
            🕉 Enter the Portal
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer style={{ textAlign: 'center', padding: '20px', borderTop: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '0.8rem', letterSpacing: '0.06em' }}>
        ॐ तत् सत् — That which is truth
      </footer>

      {/* Login Modal */}
      {showLogin && (
        <div className="viewer-modal-overlay" onClick={closeLogin}>
          <div
            className="viewer-modal"
            style={{ maxWidth: '420px' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="viewer-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <img src="/lotus.svg" alt="" style={{ width: 24, height: 24, opacity: 0.9 }} />
                <h3 style={{ fontSize: '1rem' }}>Sign In</h3>
              </div>
              <button className="btn-close" onClick={closeLogin}>✕</button>
            </div>
            <div className="viewer-modal-body" style={{ padding: '28px 24px' }}>
              {error && <div className="alert alert-error" style={{ marginBottom: '16px' }}>{error}</div>}
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
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
