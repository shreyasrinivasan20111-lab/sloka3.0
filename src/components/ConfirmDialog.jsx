export default function ConfirmDialog({ message, onConfirm, onCancel, confirmLabel = 'Confirm', danger = true }) {
  return (
    <div className="viewer-modal-overlay" onClick={onCancel}>
      <div
        className="viewer-modal"
        style={{ maxWidth: '420px' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="viewer-modal-header">
          <h3 style={{ fontSize: '1rem' }}>{danger ? '⚠️ Confirm Action' : 'Confirm'}</h3>
          <button className="btn-close" onClick={onCancel}>✕</button>
        </div>
        <div className="viewer-modal-body" style={{ padding: '28px 24px' }}>
          <p style={{ color: 'var(--text-mid)', marginBottom: '24px', lineHeight: 1.6 }}>
            {message}
          </p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
            <button
              className={danger ? 'btn btn-danger' : 'btn btn-primary'}
              onClick={onConfirm}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
