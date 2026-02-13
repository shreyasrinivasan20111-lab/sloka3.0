import { useState, useEffect } from 'react'
import { getAllSettings, setSetting } from '../../db'
import AdminLayout from '../../components/AdminLayout'

function Toggle({ label, description, checked, onChange, disabled }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      padding: '20px 0',
      borderBottom: '1px solid var(--border)',
      gap: '24px',
    }}>
      <div>
        <div style={{ fontWeight: 700, color: 'var(--text-dark)', marginBottom: '4px' }}>{label}</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{description}</div>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={onChange}
        style={{
          flexShrink: 0,
          width: '52px',
          height: '28px',
          borderRadius: '14px',
          border: 'none',
          background: checked ? 'var(--saffron)' : '#CCC',
          cursor: disabled ? 'not-allowed' : 'pointer',
          position: 'relative',
          transition: 'background 0.2s',
          outline: 'none',
        }}
      >
        <span style={{
          position: 'absolute',
          top: '3px',
          left: checked ? '26px' : '3px',
          width: '22px',
          height: '22px',
          borderRadius: '50%',
          background: 'white',
          transition: 'left 0.2s',
          boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
        }} />
      </button>
    </div>
  )
}

export default function Settings() {
  const [settings, setSettings] = useState({ portal_closed: 'false', chat_enabled: 'false' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const s = await getAllSettings()
        setSettings(s)
      } catch (err) {
        setError('Failed to load settings.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function toggle(key) {
    const newVal = settings[key] === 'true' ? 'false' : 'true'
    setSaving(key)
    setError('')
    setSuccess('')
    try {
      await setSetting(key, newVal)
      setSettings(prev => ({ ...prev, [key]: newVal }))
      setSuccess('Settings saved.')
    } catch (err) {
      setError('Failed to save setting.')
      console.error(err)
    } finally {
      setSaving(null)
    }
  }

  return (
    <AdminLayout>
      <div className="page-header">
        <div className="page-title">
          <span style={{ fontSize: '1.8rem' }}>⚙️</span>
          <h1>Portal Settings</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }} />
          <div className="spinner-text">Loading settings...</div>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            <h3>General Settings</h3>
          </div>

          <Toggle
            label="Close Portal"
            description="When enabled, students cannot log in. Admins are unaffected."
            checked={settings.portal_closed === 'true'}
            onChange={() => toggle('portal_closed')}
            disabled={saving === 'portal_closed'}
          />

          <Toggle
            label="Enable Chat Feature"
            description="Allow students to access chat within the portal (coming soon)."
            checked={settings.chat_enabled === 'true'}
            onChange={() => toggle('chat_enabled')}
            disabled={saving === 'chat_enabled'}
          />

          <div style={{ paddingTop: '24px' }}>
            <div className="alert alert-warning" style={{ marginBottom: 0 }}>
              <strong>Default Admin Credentials:</strong> username <code>admin</code> / password <code>admin123</code>.
              It is strongly recommended to change the admin password in your database.
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
