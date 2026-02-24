import { useState } from 'react'

function getFileIcon(fileType) {
  switch (fileType) {
    case 'pdf': return '📄'
    case 'doc': return '📝'
    case 'image': return '🖼'
    case 'video': return '🎬'
    case 'audio': return '🎵'
    case 'archive': return '📦'
    default: return '📎'
  }
}

function ViewerModal({ attachment, onClose }) {
  return (
    <div className="viewer-modal-overlay" onClick={onClose}>
      <div className="viewer-modal" onClick={e => e.stopPropagation()}>
        <div className="viewer-modal-header">
          <h3>
            {getFileIcon(attachment.file_type)} {attachment.label}
          </h3>
          <button className="btn-close" onClick={onClose} title="Close">✕</button>
        </div>
        <div className="viewer-modal-body">
          {attachment.file_type === 'pdf' || attachment.file_type === 'doc' ? (
            <iframe
              src={attachment.url}
              title={attachment.label}
            />
          ) : attachment.file_type === 'image' ? (
            <div style={{ padding: '24px', textAlign: 'center' }}>
              <img
                src={attachment.url}
                alt={attachment.label}
                style={{ maxWidth: '100%', maxHeight: '70vh', borderRadius: '8px' }}
              />
            </div>
          ) : attachment.file_type === 'video' ? (
            <video controls autoPlay style={{ width: '100%', maxHeight: '70vh' }}>
              <source src={attachment.url} />
              Your browser does not support the video element.
            </video>
          ) : attachment.file_type === 'audio' ? (
            <audio controls autoPlay>
              <source src={attachment.url} />
              Your browser does not support the audio element.
            </audio>
          ) : attachment.file_type === 'archive' ? (
            <div style={{ padding: '24px', textAlign: 'center' }}>
              <div style={{ fontSize: '4rem', marginBottom: '16px' }}>📦</div>
              <p style={{ marginBottom: '16px', color: 'var(--text-mid)' }}>Archive file</p>
              <a
                href={attachment.url}
                download
                className="btn btn-primary"
                onClick={(e) => e.stopPropagation()}
              >
                Download {attachment.label}
              </a>
            </div>
          ) : (
            <div style={{ padding: '24px', textAlign: 'center' }}>
              <div style={{ fontSize: '4rem', marginBottom: '16px' }}>📎</div>
              <p style={{ marginBottom: '16px', color: 'var(--text-mid)' }}>File preview not available</p>
              <a
                href={attachment.url}
                download
                className="btn btn-primary"
                onClick={(e) => e.stopPropagation()}
              >
                Download {attachment.label}
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AttachmentViewer({ attachments }) {
  const [active, setActive] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('name-asc') // name-asc, name-desc, type

  if (!attachments || attachments.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📎</div>
        <p>No attachments for this course.</p>
      </div>
    )
  }

  // Filter attachments based on search term
  const filteredAttachments = attachments.filter(att =>
    att.label.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Sort filtered attachments based on selected sort option
  const sortedAttachments = [...filteredAttachments].sort((a, b) => {
    if (sortBy === 'name-asc') {
      return a.label.localeCompare(b.label, undefined, { sensitivity: 'base' })
    } else if (sortBy === 'name-desc') {
      return b.label.localeCompare(a.label, undefined, { sensitivity: 'base' })
    } else if (sortBy === 'type') {
      // Sort by type first, then by name within each type
      const typeCompare = a.file_type.localeCompare(b.file_type)
      if (typeCompare !== 0) return typeCompare
      return a.label.localeCompare(b.label, undefined, { sensitivity: 'base' })
    }
    return 0
  })

  return (
    <>
      {/* Search and Sort Controls */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '16px',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <div style={{ flex: '1 1 200px', position: 'relative' }}>
          <input
            type="text"
            className="form-control"
            placeholder="🔍 Search attachments..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ paddingRight: searchTerm ? '32px' : '12px' }}
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                fontSize: '1.2rem',
                padding: '0 4px',
                lineHeight: 1
              }}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{
            fontSize: '0.85rem',
            color: 'var(--text-mid)',
            fontWeight: 600,
            whiteSpace: 'nowrap'
          }}>
            Sort by:
          </label>
          <select
            className="form-control"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{ width: 'auto', minWidth: '140px' }}
          >
            <option value="name-asc">Name (A-Z)</option>
            <option value="name-desc">Name (Z-A)</option>
            <option value="type">Type</option>
          </select>
        </div>
      </div>

      {/* Results count */}
      {searchTerm && (
        <div style={{
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
          marginBottom: '12px'
        }}>
          {filteredAttachments.length === 0
            ? 'No attachments found'
            : `Showing ${filteredAttachments.length} of ${attachments.length} attachment${filteredAttachments.length !== 1 ? 's' : ''}`}
        </div>
      )}

      {/* Attachment List */}
      {filteredAttachments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <p>No attachments match your search.</p>
        </div>
      ) : (
        <ul className="attachment-list">
          {sortedAttachments.map(att => (
            <li
              key={att.id}
              className="attachment-item"
              onClick={() => setActive(att)}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && setActive(att)}
            >
              <span className="attachment-icon">
                {getFileIcon(att.file_type)}
              </span>
              <span className="attachment-label">{att.label}</span>
              <span className="attachment-type">{att.file_type}</span>
            </li>
          ))}
        </ul>
      )}
      {active && <ViewerModal attachment={active} onClose={() => setActive(null)} />}
    </>
  )
}
