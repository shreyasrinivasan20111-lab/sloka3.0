import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCourseById, getAttachmentsByCourse, logCourseTime } from '../db'
import { getSession } from '../auth'
import Layout from '../components/Layout'
import AttachmentViewer from '../components/AttachmentViewer'

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

const TABS = [
  { id: 'content', label: '📖 Content' },
  { id: 'attachments', label: '📎 Attachments' },
]

export default function CourseView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const session = getSession()
  const [course, setCourse] = useState(null)
  const [attachments, setAttachments] = useState([])
  const [activeTab, setActiveTab] = useState('content')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const startTimeRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    async function load() {
      try {
        const [c, atts] = await Promise.all([
          getCourseById(id),
          getAttachmentsByCourse(id),
        ])
        if (!c) {
          setError('Course not found.')
          return
        }
        setCourse(c)
        setAttachments(atts)
      } catch (err) {
        setError('Could not load course.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Start stopwatch once course is loaded (only for students)
  useEffect(() => {
    if (!course || session?.role !== 'student') return
    startTimeRef.current = Date.now()
    intervalRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
    return () => {
      clearInterval(intervalRef.current)
      const secs = Math.floor((Date.now() - startTimeRef.current) / 1000)
      if (secs >= 1 && session?.id) {
        logCourseTime(session.id, id, secs).catch(() => {})
      }
    }
  }, [course])

  const backPath = session?.role === 'admin' ? '/admin' : '/student'

  if (loading) {
    return (
      <Layout>
        <div className="spinner-overlay" style={{ position: 'relative', background: 'none', padding: '80px 0' }}>
          <div className="spinner" />
          <div className="spinner-text">Loading course...</div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-secondary" onClick={() => navigate(backPath)}>← Back</button>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="page-header">
        <div className="page-title">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate(backPath)}
            style={{ marginRight: '8px' }}
          >
            ←
          </button>
          <h1>{course.title}</h1>
        </div>
        {session?.role === 'student' && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: 'var(--maroon)', color: 'var(--gold-light)',
            padding: '6px 14px', borderRadius: '20px',
            fontFamily: 'monospace', fontSize: '1rem', fontWeight: 700,
            letterSpacing: '0.05em', whiteSpace: 'nowrap',
          }}>
            ⏱ {formatTime(elapsed)}
          </div>
        )}
      </div>

      {course.description && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <p style={{ color: 'var(--text-mid)', fontStyle: 'italic' }}>{course.description}</p>
        </div>
      )}

      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
        {attachments.map(att => (
          <button
            key={`att-${att.id}`}
            className={`tab-btn${activeTab === `att-${att.id}` ? ' active' : ''}`}
            onClick={() => setActiveTab(`att-${att.id}`)}
          >
            {att.file_type === 'pdf' ? '📄' : '🎵'} {att.label}
          </button>
        ))}
      </div>

      <div className="card">
        {activeTab === 'content' && (
          <div>
            {course.content ? (
              <div
                className="ql-editor"
                style={{ minHeight: 'unset', padding: 0 }}
                dangerouslySetInnerHTML={{ __html: course.content }}
              />
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📝</div>
                <p>No content has been added to this course yet.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'attachments' && (
          <AttachmentViewer attachments={attachments} />
        )}

        {attachments.map(att => (
          activeTab === `att-${att.id}` && (
            <AttachmentViewer key={att.id} attachments={[att]} />
          )
        ))}
      </div>
    </Layout>
  )
}
