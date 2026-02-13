import { useState } from 'react'

function ViewerModal({ attachment, onClose }) {
  return (
    <div className="viewer-modal-overlay" onClick={onClose}>
      <div className="viewer-modal" onClick={e => e.stopPropagation()}>
        <div className="viewer-modal-header">
          <h3>
            {attachment.file_type === 'pdf' ? '📄' : '🎵'} {attachment.label}
          </h3>
          <button className="btn-close" onClick={onClose} title="Close">✕</button>
        </div>
        <div className="viewer-modal-body">
          {attachment.file_type === 'pdf' ? (
            <iframe
              src={attachment.url}
              title={attachment.label}
            />
          ) : (
            <audio controls autoPlay>
              <source src={attachment.url} />
              Your browser does not support the audio element.
            </audio>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AttachmentViewer({ attachments }) {
  const [active, setActive] = useState(null)

  if (!attachments || attachments.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📎</div>
        <p>No attachments for this course.</p>
      </div>
    )
  }

  return (
    <>
      <ul className="attachment-list">
        {attachments.map(att => (
          <li
            key={att.id}
            className="attachment-item"
            onClick={() => setActive(att)}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && setActive(att)}
          >
            <span className="attachment-icon">
              {att.file_type === 'pdf' ? '📄' : '🎵'}
            </span>
            <span className="attachment-label">{att.label}</span>
            <span className="attachment-type">{att.file_type}</span>
          </li>
        ))}
      </ul>
      {active && <ViewerModal attachment={active} onClose={() => setActive(null)} />}
    </>
  )
}
