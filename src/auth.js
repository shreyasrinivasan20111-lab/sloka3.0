const SESSION_KEY = 'sai_kalpataru_session'

export function getSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setSession(user) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({
    id: user.id,
    username: user.username,
    email: user.email,
    role: user.role,
  }))
}

export function clearSession() {
  sessionStorage.removeItem(SESSION_KEY)
}

export function isAdmin() {
  return getSession()?.role === 'admin'
}

export function isStudent() {
  return getSession()?.role === 'student'
}
