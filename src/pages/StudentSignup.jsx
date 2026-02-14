import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createSignupRequest } from '../db'
import { getSession } from '../auth'
import { Navigate } from 'react-router-dom'

export default function StudentSignup() {
  const navigate = useNavigate()
  const session = getSession()

  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  if (session) {
    return <Navigate to={session.role === 'admin' ? '/admin' : '/student'} replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!fullName.trim() || !username.trim() || !email.trim() || !password.trim()) {
      setError('All fields are required.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 4) {
      setError('Password must be at least 4 characters.')
      return
    }

    setSubmitting(true)
    try {
      await createSignupRequest(username.trim(), email.trim(), password, fullName.trim())
      setSuccess(true)
    } catch (err) {
      if (err.message?.includes('UNIQUE')) {
        setError('Username or email is already taken. Please choose another.')
      } else {
        setError('Failed to submit request. Please try again.')
      }
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(160deg, var(--cream) 0%, var(--cream-dark) 50%, #EEDED8 100%)', padding: '24px' }}>
        <div className="card" style={{ maxWidth: '460px', width: '100%', textAlign: 'center' }}>
          <img src="/lotus.svg" alt="" style={{ width: 56, margin: '0 auto 16px' }} />
          <h2 style={{ color: 'var(--maroon)', fontFamily: 'Cinzel, serif', marginBottom: '12px' }}>Request Submitted!</h2>
          <div className="alert alert-success" style={{ marginBottom: '20px' }}>
            Your registration request has been sent to the administrator. You will be notified once your account is approved.
          </div>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
            Once approved, you can log in using your username and password.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            ← Back to Home
          </button>
        </div>
      </div>
    )
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
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/')} style={{ fontWeight: 700 }}>
          ← Back
        </button>
      </header>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
        <div className="card" style={{ maxWidth: '480px', width: '100%' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>📝</span>
            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Student Sign Up</h2>
          </div>

          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>
            Submit a registration request. An administrator will review and approve your account.
          </p>

          {error && <div className="alert alert-error" style={{ marginBottom: '16px' }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="fullName">Full Name</label>
              <input
                id="fullName"
                className="form-control"
                type="text"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                placeholder="Your full name"
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                className="form-control"
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Choose a username"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                className="form-control"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
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
                placeholder="Choose a password"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                id="confirmPassword"
                className="form-control"
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                required
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
              disabled={submitting}
            >
              {submitting ? 'Submitting...' : '📨 Submit Registration Request'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Already have an account?{' '}
              <button
                className="btn-link"
                style={{ color: 'var(--saffron-dark)', fontWeight: 700, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontSize: '0.9rem' }}
                onClick={() => navigate('/')}
              >
                Sign In
              </button>
            </span>
          </div>
        </div>
      </div>

      <footer style={{ textAlign: 'center', padding: '20px', borderTop: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '0.8rem', letterSpacing: '0.06em' }}>
        ॐ तत् सत् — That which is truth
      </footer>
    </div>
  )
}
