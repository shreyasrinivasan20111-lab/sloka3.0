import { useState, useEffect } from 'react'
import {
  getAllStudents, createStudent, deleteStudent, updateStudentPassword,
  getPendingStudents, approveStudent, rejectStudent, getStudentTimeSummary,
} from '../../db'
import AdminLayout from '../../components/AdminLayout'
import ConfirmDialog from '../../components/ConfirmDialog'

function formatSeconds(total) {
  if (!total || total < 1) return '0m 0s'
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h > 0) return `${h}h ${m}m ${s}s`
  return `${m}m ${s}s`
}

export default function StudentManagement() {
  const [students, setStudents] = useState([])
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Create form
  const [showForm, setShowForm] = useState(false)
  const [newUsername, setNewUsername] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [creating, setCreating] = useState(false)

  // Password reset
  const [resetFor, setResetFor] = useState(null)
  const [resetPwd, setResetPwd] = useState('')
  const [confirmDialog, setConfirmDialog] = useState(null)

  // Time modal
  const [timeModal, setTimeModal] = useState(null) // { student }
  const [timeSummary, setTimeSummary] = useState([])
  const [timeLoading, setTimeLoading] = useState(false)

  async function load() {
    try {
      const [data, pend] = await Promise.all([getAllStudents(), getPendingStudents()])
      setStudents(data)
      setPending(pend)
    } catch (err) {
      setError('Failed to load students.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleCreate(e) {
    e.preventDefault()
    if (!newUsername.trim() || !newEmail.trim() || !newPassword.trim()) {
      setError('All fields are required.')
      return
    }
    setCreating(true)
    setError('')
    try {
      await createStudent(newUsername.trim(), newEmail.trim(), newPassword.trim())
      setSuccess(`Student "${newUsername}" created.`)
      setNewUsername('')
      setNewEmail('')
      setNewPassword('')
      setShowForm(false)
      await load()
    } catch (err) {
      if (err.message?.includes('UNIQUE')) {
        setError('Username or email already exists.')
      } else {
        setError('Failed to create student.')
      }
      console.error(err)
    } finally {
      setCreating(false)
    }
  }

  function handleDelete(student) {
    setConfirmDialog({
      message: `Delete student "${student.username}"? This will remove all their course assignments.`,
      onConfirm: async () => {
        setConfirmDialog(null)
        try {
          await deleteStudent(student.id)
          setStudents(prev => prev.filter(s => s.id !== student.id))
          setSuccess(`Student "${student.username}" deleted.`)
        } catch (err) {
          setError('Failed to delete student.')
        }
      },
    })
  }

  async function handleResetPassword(e) {
    e.preventDefault()
    if (!resetPwd.trim()) { setError('Password cannot be empty.'); return }
    try {
      await updateStudentPassword(resetFor.id, resetPwd.trim())
      setSuccess(`Password updated for "${resetFor.username}".`)
      setResetFor(null)
      setResetPwd('')
    } catch (err) {
      setError('Failed to update password.')
    }
  }

  async function handleApprove(student) {
    try {
      await approveStudent(student.id)
      setPending(prev => prev.filter(s => s.id !== student.id))
      setSuccess(`"${student.username}" approved and can now log in.`)
      await load()
    } catch (err) {
      setError('Failed to approve student.')
    }
  }

  function handleReject(student) {
    setConfirmDialog({
      message: `Reject and delete signup request from "${student.username}"?`,
      onConfirm: async () => {
        setConfirmDialog(null)
        try {
          await rejectStudent(student.id)
          setPending(prev => prev.filter(s => s.id !== student.id))
          setSuccess(`Signup request from "${student.username}" rejected.`)
        } catch (err) {
          setError('Failed to reject request.')
        }
      },
    })
  }

  async function openTimeModal(student) {
    setTimeModal({ student })
    setTimeLoading(true)
    try {
      const summary = await getStudentTimeSummary(student.id)
      setTimeSummary(summary)
    } catch (err) {
      setTimeSummary([])
    } finally {
      setTimeLoading(false)
    }
  }

  return (
    <AdminLayout>
      <div className="page-header">
        <div className="page-title">
          <span style={{ fontSize: '1.8rem' }}>👥</span>
          <h1>Student Management</h1>
        </div>
        <button className="btn btn-primary" onClick={() => { setShowForm(v => !v); setError('') }}>
          {showForm ? '✕ Cancel' : '➕ New Student'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Pending Approvals */}
      {pending.length > 0 && (
        <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--saffron)' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.2rem' }}>⏳</span>
            <h3 style={{ margin: 0 }}>Pending Approvals ({pending.length})</h3>
          </div>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Full Name</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Requested</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pending.map(s => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.full_name || '—'}</td>
                    <td>{s.username}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{s.email}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleApprove(s)}
                        >
                          ✔ Approve
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleReject(s)}
                        >
                          ✕ Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Student Form */}
      {showForm && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header"><h3>Create Student Account</h3></div>
          <form onSubmit={handleCreate}>
            <div className="form-grid-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Username</label>
                <input
                  className="form-control"
                  value={newUsername}
                  onChange={e => setNewUsername(e.target.value)}
                  placeholder="arjuna"
                  required
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Email</label>
                <input
                  className="form-control"
                  type="email"
                  value={newEmail}
                  onChange={e => setNewEmail(e.target.value)}
                  placeholder="arjuna@example.com"
                  required
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Password</label>
                <input
                  className="form-control"
                  type="text"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Initial password"
                  required
                />
              </div>
            </div>
            <div style={{ marginTop: '16px' }}>
              <button type="submit" className="btn btn-primary" disabled={creating}>
                {creating ? 'Creating...' : '✔ Create Student'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Students Table */}
      <div className="card">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <div className="spinner" style={{ margin: '0 auto 12px' }} />
            <div className="spinner-text">Loading students...</div>
          </div>
        ) : students.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👥</div>
            <p>No students yet. Create the first student account.</p>
          </div>
        ) : (
          <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Username</th>
                <th>Email</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s, i) => (
                <tr key={s.id}>
                  <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                  <td>
                    <span style={{ fontWeight: 700 }}>{s.username}</span>
                    {s.full_name && (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{s.full_name}</div>
                    )}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{s.email}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {new Date(s.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => openTimeModal(s)}
                      >
                        ⏱ Time
                      </button>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => { setResetFor(s); setResetPwd(''); setError('') }}
                      >
                        🔑 Password
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(s)}
                      >
                        🗑 Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>

      {/* Confirm Dialog */}
      {confirmDialog && (
        <ConfirmDialog
          message={confirmDialog.message}
          confirmLabel="Confirm"
          onConfirm={confirmDialog.onConfirm}
          onCancel={() => setConfirmDialog(null)}
        />
      )}

      {/* Reset Password Modal */}
      {resetFor && (
        <div className="viewer-modal-overlay" onClick={() => setResetFor(null)}>
          <div
            className="viewer-modal"
            style={{ maxWidth: '400px' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="viewer-modal-header">
              <h3>🔑 Reset Password: {resetFor.username}</h3>
              <button className="btn-close" onClick={() => setResetFor(null)}>✕</button>
            </div>
            <div className="viewer-modal-body" style={{ padding: '24px' }}>
              <form onSubmit={handleResetPassword}>
                <div className="form-group">
                  <label>New Password</label>
                  <input
                    className="form-control"
                    type="text"
                    value={resetPwd}
                    onChange={e => setResetPwd(e.target.value)}
                    placeholder="Enter new password"
                    required
                    autoFocus
                  />
                </div>
                <button type="submit" className="btn btn-primary">
                  ✔ Update Password
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Time Modal */}
      {timeModal && (
        <div className="viewer-modal-overlay" onClick={() => setTimeModal(null)}>
          <div
            className="viewer-modal"
            style={{ maxWidth: '520px' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="viewer-modal-header">
              <h3>⏱ Time Report: {timeModal.student.username}</h3>
              <button className="btn-close" onClick={() => setTimeModal(null)}>✕</button>
            </div>
            <div className="viewer-modal-body" style={{ padding: '24px', overflowY: 'auto', maxHeight: '60vh' }}>
              {timeLoading ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <div className="spinner" style={{ margin: '0 auto' }} />
                </div>
              ) : timeSummary.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">⏱</div>
                  <p>No time logged yet for this student.</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Course</th>
                        <th style={{ textAlign: 'right' }}>Total Time Spent</th>
                      </tr>
                    </thead>
                    <tbody>
                      {timeSummary.map((row, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: 600 }}>{row.title}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'monospace', color: 'var(--saffron-dark)', fontWeight: 700 }}>
                            {formatSeconds(Number(row.total_seconds))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
