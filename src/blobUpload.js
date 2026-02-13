import { put } from '@vercel/blob'

/**
 * Upload a file to Vercel Blob and return its URL.
 * @param {File} file - The file to upload
 * @param {string} folder - Folder prefix (e.g. 'attachments')
 * @returns {Promise<string>} - The public URL
 */
export async function uploadFile(file, folder = 'attachments') {
  const filename = `${folder}/${Date.now()}-${file.name.replace(/\s+/g, '_')}`
  const blob = await put(filename, file, {
    access: 'public',
    token: import.meta.env.VITE_BLOB_READ_WRITE_TOKEN,
  })
  return blob.url
}

/**
 * Detect file type from MIME or extension.
 * @param {File} file
 * @returns {'pdf' | 'audio' | 'unknown'}
 */
export function detectFileType(file) {
  if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) return 'pdf'
  if (file.type.startsWith('audio/') || /\.(mp3|wav|ogg|aac|m4a)$/i.test(file.name)) return 'audio'
  return 'unknown'
}
