import { useState, useEffect } from 'react'
import { getSession } from '../../auth'
import {
  getCoursesCreatedByAdmin,
  getAssignedStudents,
  getAttendanceByDateAndCourse,
  bulkSaveAttendance,
  getAttendanceByMonth,
} from '../../db'
import AdminLayout from '../../components/AdminLayout'

function getTodayDate() {
  return new Date().toISOString().split('T')[0] // YYYY-MM-DD format
}

function formatDateForDisplay(dateStr) {
  // Convert YYYY-MM-DD to MM/DD/YYYY
  const [year, month, day] = dateStr.split('-')
  return `${month}/${day}/${year}`
}

export default function AttendanceManagement() {
  const session = getSession()

  // Tab management
  const [activeTab, setActiveTab] = useState('take') // 'take' | 'view'

  // Common
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Take Attendance
  const [selectedDate, setSelectedDate] = useState(getTodayDate())
  const [selectedCourseId, setSelectedCourseId] = useState('')
  const [students, setStudents] = useState([])
  const [attendanceMap, setAttendanceMap] = useState({}) // { studentId: 'present'|'absent'|'late' }
  const [saving, setSaving] = useState(false)

  // View Records
  const [viewMonth, setViewMonth] = useState(new Date().getMonth() + 1)
  const [viewYear, setViewYear] = useState(new Date().getFullYear())
  const [viewCourseId, setViewCourseId] = useState('')
  const [attendanceRecords, setAttendanceRecords] = useState([])
  const [viewLoading, setViewLoading] = useState(false)

  // Sorting & Filtering
  const [sortField, setSortField] = useState('date') // 'date' | 'student' | 'status'
  const [sortDirection, setSortDirection] = useState('desc') // 'asc' | 'desc'
  const [dateFilter, setDateFilter] = useState('')
  const [studentFilter, setStudentFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('') // '' | 'present' | 'late' | 'absent'

  // Load courses on mount
  useEffect(() => {
    async function loadCourses() {
      try {
        const data = await getCoursesCreatedByAdmin(session.id)
        setCourses(data)
        if (data.length > 0) {
          setSelectedCourseId(data[0].id)
          setViewCourseId(data[0].id)
        }
      } catch (err) {
        setError('Failed to load courses.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadCourses()
  }, [])

  // Load students + existing attendance when date/course changes
  useEffect(() => {
    if (!selectedCourseId || !selectedDate) return
    async function loadAttendanceData() {
      try {
        const [studentsData, attendanceData] = await Promise.all([
          getAssignedStudents(selectedCourseId),
          getAttendanceByDateAndCourse(selectedDate, selectedCourseId)
        ])

        // Sort alphabetically by full_name or username
        const sorted = studentsData.sort((a, b) =>
          (a.full_name || a.username).localeCompare(b.full_name || b.username)
        )
        setStudents(sorted)

        // Build map from existing attendance, default to 'present'
        const map = {}
        attendanceData.forEach(record => {
          map[record.student_id] = record.status
        })
        sorted.forEach(student => {
          if (!map[student.id]) map[student.id] = 'present'
        })
        setAttendanceMap(map)
      } catch (err) {
        setError('Failed to load attendance data.')
        console.error(err)
      }
    }
    loadAttendanceData()
  }, [selectedCourseId, selectedDate])

  // Load records for View tab
  useEffect(() => {
    if (activeTab !== 'view' || !viewCourseId) return
    async function loadRecords() {
      setViewLoading(true)
      try {
        const records = await getAttendanceByMonth(viewCourseId, viewYear, viewMonth)
        setAttendanceRecords(records)
      } catch (err) {
        setError('Failed to load attendance records.')
        console.error(err)
      } finally {
        setViewLoading(false)
      }
    }
    loadRecords()
  }, [activeTab, viewCourseId, viewMonth, viewYear])

  async function handleSaveAttendance() {
    if (!selectedCourseId || !selectedDate) {
      setError('Please select date and course.')
      return
    }
    if (students.length === 0) {
      setError('No students assigned to this course.')
      return
    }

    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const records = students.map(s => ({
        courseId: selectedCourseId,
        studentId: s.id,
        date: selectedDate,
        status: attendanceMap[s.id],
        markedBy: session.id,
      }))
      await bulkSaveAttendance(records)
      setSuccess(`Attendance saved for ${students.length} students on ${formatDateForDisplay(selectedDate)}`)
    } catch (err) {
      setError('Failed to save attendance.')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  function renderTakeAttendance() {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          <div className="spinner-text">Loading courses...</div>
        </div>
      )
    }

    if (courses.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <p>No courses found. Create a course first.</p>
        </div>
      )
    }

    return (
      <div className="card">
        {/* Date + Course Selectors */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div className="form-group">
            <label>Date</label>
            <input
              type="date"
              className="form-control"
              value={selectedDate}
              onChange={e => setSelectedDate(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Course</label>
            <select
              className="form-control"
              value={selectedCourseId}
              onChange={e => setSelectedCourseId(e.target.value)}
            >
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Students Table */}
        {students.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👥</div>
            <p>No students assigned to this course.</p>
          </div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Student Name</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s, i) => (
                    <tr key={s.id}>
                      <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                      <td>
                        <span style={{ fontWeight: 600 }}>
                          {s.full_name || s.username}
                        </span>
                      </td>
                      <td>
                        <select
                          className="form-control"
                          style={{ maxWidth: '150px' }}
                          value={attendanceMap[s.id]}
                          onChange={e => setAttendanceMap({
                            ...attendanceMap,
                            [s.id]: e.target.value
                          })}
                        >
                          <option value="present">✅ Present</option>
                          <option value="late">⏰ Late</option>
                          <option value="absent">❌ Absent</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: '24px' }}>
              <button
                className="btn btn-primary"
                onClick={handleSaveAttendance}
                disabled={saving}
              >
                {saving ? 'Saving...' : '💾 Save Attendance'}
              </button>
            </div>
          </>
        )}
      </div>
    )
  }

  function handleSort(field) {
    if (sortField === field) {
      // Toggle direction if clicking same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      // New field, default to ascending
      setSortField(field)
      setSortDirection('asc')
    }
  }

  function getFilteredAndSortedRecords() {
    let filtered = [...attendanceRecords]

    // Apply filters
    if (dateFilter) {
      filtered = filtered.filter(record =>
        formatDateForDisplay(record.date).toLowerCase().includes(dateFilter.toLowerCase())
      )
    }
    if (studentFilter) {
      filtered = filtered.filter(record =>
        (record.full_name || record.username).toLowerCase().includes(studentFilter.toLowerCase())
      )
    }
    if (statusFilter) {
      filtered = filtered.filter(record => record.status === statusFilter)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal, bVal

      if (sortField === 'date') {
        aVal = a.date
        bVal = b.date
      } else if (sortField === 'student') {
        aVal = (a.full_name || a.username).toLowerCase()
        bVal = (b.full_name || b.username).toLowerCase()
      } else if (sortField === 'status') {
        aVal = a.status
        bVal = b.status
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })

    return filtered
  }

  function renderViewRecords() {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December']
    const years = [viewYear - 2, viewYear - 1, viewYear, viewYear + 1, viewYear + 2]

    const filteredRecords = getFilteredAndSortedRecords()

    return (
      <div className="card">
        {/* Month/Year/Course Selectors */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div className="form-group">
            <label>Month</label>
            <select
              className="form-control"
              value={viewMonth}
              onChange={e => setViewMonth(Number(e.target.value))}
            >
              {months.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Year</label>
            <select
              className="form-control"
              value={viewYear}
              onChange={e => setViewYear(Number(e.target.value))}
            >
              {years.map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Course</label>
            <select
              className="form-control"
              value={viewCourseId}
              onChange={e => setViewCourseId(e.target.value)}
            >
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Column Filters */}
        {attendanceRecords.length > 0 && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: '16px',
            marginBottom: '16px',
            padding: '16px',
            background: '#f8f9fa',
            borderRadius: '8px'
          }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Filter by Date</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g., 02/25"
                value={dateFilter}
                onChange={e => setDateFilter(e.target.value)}
                style={{ fontSize: '0.9rem' }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Filter by Student</label>
              <input
                type="text"
                className="form-control"
                placeholder="Student name"
                value={studentFilter}
                onChange={e => setStudentFilter(e.target.value)}
                style={{ fontSize: '0.9rem' }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Filter by Status</label>
              <select
                className="form-control"
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                style={{ fontSize: '0.9rem' }}
              >
                <option value="">All</option>
                <option value="present">Present</option>
                <option value="late">Late</option>
                <option value="absent">Absent</option>
              </select>
            </div>
          </div>
        )}

        {/* Clear Filters Button */}
        {(dateFilter || studentFilter || statusFilter) && (
          <div style={{ marginBottom: '16px' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setDateFilter('')
                setStudentFilter('')
                setStatusFilter('')
              }}
            >
              ✕ Clear Filters
            </button>
          </div>
        )}

        {/* Records Table */}
        {viewLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div className="spinner" style={{ margin: '0 auto 12px' }} />
            <div className="spinner-text">Loading records...</div>
          </div>
        ) : attendanceRecords.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📅</div>
            <p>No attendance records for {months[viewMonth - 1]} {viewYear}.</p>
          </div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th
                      onClick={() => handleSort('date')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      Date {sortField === 'date' && (sortDirection === 'asc' ? '▲' : '▼')}
                    </th>
                    <th
                      onClick={() => handleSort('student')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      Student {sortField === 'student' && (sortDirection === 'asc' ? '▲' : '▼')}
                    </th>
                    <th
                      onClick={() => handleSort('status')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      Status {sortField === 'status' && (sortDirection === 'asc' ? '▲' : '▼')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.length === 0 ? (
                    <tr>
                      <td colSpan="3" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                        No records match your filters
                      </td>
                    </tr>
                  ) : (
                    filteredRecords.map(record => (
                      <tr key={record.id}>
                        <td>{formatDateForDisplay(record.date)}</td>
                        <td style={{ fontWeight: 600 }}>
                          {record.full_name || record.username}
                        </td>
                        <td>
                          <span style={{
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '0.85rem',
                            fontWeight: 600,
                            backgroundColor:
                              record.status === 'present' ? '#d4edda' :
                              record.status === 'late' ? '#fff3cd' : '#f8d7da',
                            color:
                              record.status === 'present' ? '#155724' :
                              record.status === 'late' ? '#856404' : '#721c24'
                          }}>
                            {record.status === 'present' ? '✅ Present' :
                             record.status === 'late' ? '⏰ Late' : '❌ Absent'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Results Counter */}
            <div style={{
              marginTop: '12px',
              fontSize: '0.85rem',
              color: 'var(--text-muted)',
              textAlign: 'right'
            }}>
              Showing {filteredRecords.length} of {attendanceRecords.length} records
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <AdminLayout>
      {/* Page Header */}
      <div className="page-header">
        <div className="page-title">
          <span style={{ fontSize: '1.8rem' }}>📋</span>
          <h1>Attendance Management</h1>
        </div>
      </div>

      {/* Alerts */}
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '24px',
        borderBottom: '2px solid var(--border)'
      }}>
        <button
          className={`tab-btn ${activeTab === 'take' ? 'active' : ''}`}
          onClick={() => setActiveTab('take')}
          style={{
            padding: '12px 24px',
            background: activeTab === 'take' ? 'var(--saffron)' : 'transparent',
            color: activeTab === 'take' ? 'white' : 'inherit',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            borderRadius: '4px 4px 0 0',
          }}
        >
          ✏️ Take Attendance
        </button>
        <button
          className={`tab-btn ${activeTab === 'view' ? 'active' : ''}`}
          onClick={() => setActiveTab('view')}
          style={{
            padding: '12px 24px',
            background: activeTab === 'view' ? 'var(--saffron)' : 'transparent',
            color: activeTab === 'view' ? 'white' : 'inherit',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            borderRadius: '4px 4px 0 0',
          }}
        >
          📅 View Records
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'take' ? renderTakeAttendance() : renderViewRecords()}
    </AdminLayout>
  )
}
