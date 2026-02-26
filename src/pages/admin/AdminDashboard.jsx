import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAllCourses, deleteCourse, getAllStudents, getAssignedStudents, assignCourse, unassignCourse } from '../../db'
import AdminLayout from '../../components/AdminLayout'
import ConfirmDialog from '../../components/ConfirmDialog'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [courses, setCourses] = useState([])
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [assignModal, setAssignModal] = useState(null) // { course }
  const [assignedIds, setAssignedIds] = useState([])
  const [assignLoading, setAssignLoading] = useState(false)
  const [confirmDialog, setConfirmDialog] = useState(null) // { message, onConfirm }
  const [sortBy, setSortBy] = useState('date') // 'date' | 'a-z' | 'z-a'

  async function load() {
    try {
      const [c, s] = await Promise.all([getAllCourses(), getAllStudents()])
      setCourses(c)
      setStudents(s)
    } catch (err) {
      setError('Failed to load data.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function handleDelete(course) {
    setConfirmDialog({
      message: `Delete course "${course.title}"? This cannot be undone.`,
      onConfirm: async () => {
        setConfirmDialog(null)
        try {
          await deleteCourse(course.id)
          setCourses(prev => prev.filter(c => c.id !== course.id))
        } catch (err) {
          setError('Failed to delete course.')
        }
      },
    })
  }

  async function openAssign(course) {
    setAssignModal({ course })
    setAssignLoading(true)
    try {
      const assigned = await getAssignedStudents(course.id)
      setAssignedIds(assigned.map(s => s.id))
    } finally {
      setAssignLoading(false)
    }
  }

  async function toggleAssign(studentId) {
    const courseId = assignModal.course.id
    if (assignedIds.includes(studentId)) {
      await unassignCourse(courseId, studentId)
      setAssignedIds(prev => prev.filter(id => id !== studentId))
    } else {
      await assignCourse(courseId, studentId)
      setAssignedIds(prev => [...prev, studentId])
    }
  }

  function getSortedCourses() {
    const sorted = [...courses]

    if (sortBy === 'a-z') {
      sorted.sort((a, b) => a.title.localeCompare(b.title))
    } else if (sortBy === 'z-a') {
      sorted.sort((a, b) => b.title.localeCompare(a.title))
    } else if (sortBy === 'date') {
      // Default: newest first (descending by created_at)
      sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    }

    return sorted
  }

  return (
    <AdminLayout>
      <div className="page-header">
        <div className="page-title">
          <span style={{ fontSize: '1.8rem' }}>📚</span>
          <h1>All Courses</h1>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/admin/courses/new')}>
          ➕ New Course
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }} />
          <div className="spinner-text">Loading courses...</div>
        </div>
      ) : courses.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <p>No courses yet. Create your first course!</p>
          <button className="btn btn-primary" onClick={() => navigate('/admin/courses/new')}>
            ➕ Create Course
          </button>
        </div>
      ) : (
        <>
          {/* Sorting Controls */}
          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            marginBottom: '16px',
            gap: '12px'
          }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Sort by:
            </label>
            <select
              className="form-control"
              style={{ width: 'auto', minWidth: '180px' }}
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
            >
              <option value="date">📅 Date (Newest First)</option>
              <option value="a-z">🔤 A to Z</option>
              <option value="z-a">🔤 Z to A</option>
            </select>
          </div>

          <div className="course-grid">
            {getSortedCourses().map(course => (
            <div key={course.id} className="course-card">
              <div
                className="course-card-header"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/student/course/${course.id}`)}
              >
                <h3>{course.title}</h3>
                {course.description && <p>{course.description}</p>}
              </div>
              <div className="course-card-body">
                <small style={{ color: 'var(--text-muted)' }}>
                  📅 {new Date(course.created_at).toLocaleDateString()}
                </small>
              </div>
              <div className="course-card-footer">
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => navigate(`/admin/courses/${course.id}/edit`)}
                  >
                    ✏️ Edit
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => openAssign(course)}
                  >
                    👥 Assign
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(course)}
                  >
                    🗑 Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
          </div>
        </>
      )}

      {/* Confirm Dialog */}
      {confirmDialog && (
        <ConfirmDialog
          message={confirmDialog.message}
          confirmLabel="Delete"
          onConfirm={confirmDialog.onConfirm}
          onCancel={() => setConfirmDialog(null)}
        />
      )}

      {/* Assign Modal */}
      {assignModal && (
        <div className="viewer-modal-overlay" onClick={() => setAssignModal(null)}>
          <div className="viewer-modal" style={{ maxWidth: '520px' }} onClick={e => e.stopPropagation()}>
            <div className="viewer-modal-header">
              <h3>👥 Assign: <span className="course-title">{assignModal.course.title}</span></h3>
              <button className="btn-close" onClick={() => setAssignModal(null)}>✕</button>
            </div>
            <div className="viewer-modal-body" style={{ padding: '24px', overflowY: 'auto', maxHeight: '60vh' }}>
              {assignLoading ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <div className="spinner" style={{ margin: '0 auto' }} />
                </div>
              ) : students.length === 0 ? (
                <div className="empty-state">
                  <p>No students found. Create students first.</p>
                </div>
              ) : (
                <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Email</th>
                      <th>Assigned</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map(s => (
                      <tr key={s.id}>
                        <td>{s.username}</td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{s.email}</td>
                        <td>
                          <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <input
                              type="checkbox"
                              checked={assignedIds.includes(s.id)}
                              onChange={() => toggleAssign(s.id)}
                              style={{ width: '16px', height: '16px', accentColor: 'var(--saffron)' }}
                            />
                            {assignedIds.includes(s.id) ? (
                              <span style={{ color: 'var(--saffron-dark)', fontWeight: 700, fontSize: '0.8rem' }}>Assigned</span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Unassigned</span>
                            )}
                          </label>
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
