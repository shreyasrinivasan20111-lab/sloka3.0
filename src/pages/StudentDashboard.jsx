import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAssignedCourses } from '../db'
import { getSession } from '../auth'
import Layout from '../components/Layout'

export default function StudentDashboard() {
  const session = getSession()
  const navigate = useNavigate()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const data = await getAssignedCourses(session.id)
        setCourses(data)
      } catch (err) {
        setError('Could not load courses. Please refresh.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [session.id])

  return (
    <Layout>
      <div className="page-header">
        <div className="page-title">
          <span style={{ fontSize: '1.8rem' }}>🙏</span>
          <h1>My Sacred Courses</h1>
        </div>
      </div>

      <div className="divider">
        <span>✦</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="spinner-overlay" style={{ position: 'relative', background: 'none', padding: '60px 0' }}>
          <div className="spinner" />
          <div className="spinner-text">Loading your courses...</div>
        </div>
      ) : courses.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <p>No courses have been assigned to you yet.</p>
          <small style={{ color: 'var(--text-muted)' }}>Please contact your administrator.</small>
        </div>
      ) : (
        <div className="course-grid">
          {courses.map(course => (
            <div
              key={course.id}
              className="course-card"
              onClick={() => navigate(`/student/course/${course.id}`)}
            >
              <div className="course-card-header">
                <h3>{course.title}</h3>
                {course.description && <p>{course.description}</p>}
              </div>
              <div className="course-card-footer">
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  📅 {new Date(course.created_at).toLocaleDateString()}
                </span>
                <span className="btn btn-primary btn-sm">Open →</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
