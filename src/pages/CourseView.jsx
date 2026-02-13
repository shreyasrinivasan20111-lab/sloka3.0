import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCourseById, getAttachmentsByCourse } from '../db'
import { getSession } from '../auth'
import Layout from '../components/Layout'
import AttachmentViewer from '../components/AttachmentViewer'

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
