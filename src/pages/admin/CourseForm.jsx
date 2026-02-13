import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import {
  getCourseById,
  createCourse,
  updateCourse,
  getAttachmentsByCourse,
  addAttachment,
  deleteAttachment,
} from '../../db'
import { uploadFile, detectFileType } from '../../blobUpload'
import { getSession } from '../../auth'
import AdminLayout from '../../components/AdminLayout'

const QUILL_MODULES = {
  toolbar: [
    [{ header: [1, 2, 3, false] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ list: 'ordered' }, { list: 'bullet' }],
    [{ color: [] }, { background: [] }],
    ['blockquote', 'code-block'],
    ['link'],
    ['clean'],
  ],
}

export default function CourseForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const session = getSession()
  const isEdit = Boolean(id)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [content, setContent] = useState('')
  const [attachments, setAttachments] = useState([]) // existing from DB
  const [newFiles, setNewFiles] = useState([]) // { file, label, uploading, error }
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const fileInputRef = useRef()

  useEffect(() => {
    if (!isEdit) return
    async function load() {
      try {
        const [course, atts] = await Promise.all([
          getCourseById(id),
          getAttachmentsByCourse(id),
        ])
        if (!course) { setError('Course not found.'); return }
        setTitle(course.title)
        setDescription(course.description || '')
        setContent(course.content || '')
        setAttachments(atts)
      } catch (err) {
        setError('Failed to load course.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id, isEdit])

  function handleFileAdd(e) {
    const files = Array.from(e.target.files)
    const valid = files.filter(f => {
      const t = detectFileType(f)
      return t === 'pdf' || t === 'audio'
    })
    if (valid.length !== files.length) {
      setError('Only PDF and audio files are allowed.')
    }
    const entries = valid.map(file => ({
      file,
      label: file.name.replace(/\.[^.]+$/, ''),
      uploading: false,
      error: null,
      id: Math.random().toString(36).slice(2),
    }))
    setNewFiles(prev => [...prev, ...entries])
    fileInputRef.current.value = ''
  }

  function updateNewFileLabel(idx, label) {
    setNewFiles(prev => prev.map((f, i) => i === idx ? { ...f, label } : f))
  }

  function removeNewFile(idx) {
    setNewFiles(prev => prev.filter((_, i) => i !== idx))
  }

  async function handleDeleteExisting(att) {
    if (!confirm(`Remove attachment "${att.label}"?`)) return
    try {
      await deleteAttachment(att.id)
      setAttachments(prev => prev.filter(a => a.id !== att.id))
    } catch (err) {
      setError('Failed to remove attachment.')
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim()) { setError('Title is required.'); return }
    setError('')
    setSaving(true)
    setSuccess('')
    try {
      let courseId = id
      if (isEdit) {
        await updateCourse(id, title.trim(), description.trim(), content)
      } else {
        courseId = await createCourse(title.trim(), description.trim(), content, session.id)
        courseId = Number(courseId)
      }

      // Upload new files
      for (let i = 0; i < newFiles.length; i++) {
        const entry = newFiles[i]
        setNewFiles(prev => prev.map((f, idx) => idx === i ? { ...f, uploading: true } : f))
        try {
          const url = await uploadFile(entry.file)
          const fileType = detectFileType(entry.file)
          await addAttachment(courseId, entry.label || entry.file.name, url, fileType)
          setNewFiles(prev => prev.map((f, idx) => idx === i ? { ...f, uploading: false } : f))
        } catch (err) {
          setNewFiles(prev => prev.map((f, idx) => idx === i ? { ...f, uploading: false, error: 'Upload failed' } : f))
          console.error(err)
        }
      }

      setSuccess(isEdit ? 'Course updated successfully!' : 'Course created successfully!')
      if (!isEdit) {
        setTimeout(() => navigate('/admin'), 1000)
      } else {
        // Refresh attachments
        const atts = await getAttachmentsByCourse(courseId)
        setAttachments(atts)
        setNewFiles([])
      }
    } catch (err) {
      setError('Failed to save course. Please try again.')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <AdminLayout>
      <div className="page-header">
        <div className="page-title">
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/admin')} style={{ marginRight: '8px' }}>←</button>
          <h1>{isEdit ? '✏️ Edit Course' : '➕ New Course'}</h1>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }} />
          <div className="spinner-text">Loading course...</div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3>Course Details</h3>
            </div>

            <div className="form-group">
              <label>Title *</label>
              <input
                className="form-control"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g. Introduction to Vedanta"
                required
              />
            </div>

            <div className="form-group">
              <label>Short Description</label>
              <textarea
                className="form-control"
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="A brief overview of the course..."
                rows={3}
              />
            </div>

            <div className="form-group">
              <label>Course Content</label>
              <ReactQuill
                theme="snow"
                value={content}
                onChange={setContent}
                modules={QUILL_MODULES}
                placeholder="Enter the sacred knowledge here..."
              />
            </div>
          </div>

          {/* Existing Attachments */}
          {isEdit && attachments.length > 0 && (
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <h3>📎 Existing Attachments</h3>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Label</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {attachments.map(att => (
                    <tr key={att.id}>
                      <td>{att.file_type === 'pdf' ? '📄 PDF' : '🎵 Audio'}</td>
                      <td>{att.label}</td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDeleteExisting(att)}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* New Attachments */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3>📎 Add Attachments</h3>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => fileInputRef.current.click()}
              >
                + Choose Files
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,audio/*"
              multiple
              style={{ display: 'none' }}
              onChange={handleFileAdd}
            />

            {newFiles.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '8px' }}>
                No new files selected. Click "Choose Files" to add PDF or audio attachments.
              </p>
            ) : (
              <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {newFiles.map((entry, idx) => (
                  <div key={entry.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 14px',
                    background: 'var(--cream)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                  }}>
                    <span>{detectFileType(entry.file) === 'pdf' ? '📄' : '🎵'}</span>
                    <input
                      className="form-control"
                      style={{ flex: 1 }}
                      value={entry.label}
                      onChange={e => updateNewFileLabel(idx, e.target.value)}
                      placeholder="Label for this attachment"
                    />
                    <small style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {(entry.file.size / 1024).toFixed(0)} KB
                    </small>
                    {entry.uploading && <span style={{ color: 'var(--saffron)' }}>⏳</span>}
                    {entry.error && <span style={{ color: 'red', fontSize: '0.8rem' }}>{entry.error}</span>}
                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      onClick={() => removeNewFile(idx)}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? '⏳ Saving...' : (isEdit ? '✔ Update Course' : '✔ Create Course')}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/admin')}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </AdminLayout>
  )
}
