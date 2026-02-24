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
 * @returns {'pdf' | 'doc' | 'image' | 'video' | 'audio' | 'archive' | 'unknown'}
 */
export function detectFileType(file) {
  // PDF
  if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) return 'pdf'

  // Word documents
  if (
    file.type === 'application/msword' ||
    file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
    /\.(doc|docx)$/i.test(file.name)
  ) return 'doc'

  // Images
  if (
    file.type.startsWith('image/') ||
    /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(file.name)
  ) return 'image'

  // Video
  if (
    file.type.startsWith('video/') ||
    /\.(mp4|avi|mov|wmv|flv|webm|mkv)$/i.test(file.name)
  ) return 'video'

  // Audio
  if (
    file.type.startsWith('audio/') ||
    /\.(mp3|wav|ogg|aac|m4a|flac|wma)$/i.test(file.name)
  ) return 'audio'

  // Archives
  if (
    file.type === 'application/zip' ||
    file.type === 'application/x-rar-compressed' ||
    file.type === 'application/x-rar' ||
    /\.(zip|rar|7z|tar|gz)$/i.test(file.name)
  ) return 'archive'

  return 'unknown'
}
