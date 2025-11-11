import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [staff, setStaff] = useState<any[]>([])
  const [patients, setPatients] = useState<any[]>([])
  const [tasks, setTasks] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState('status')

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (!token || !userData) {
      router.push('/')
      return
    }

    setUser(JSON.parse(userData))
    loadData()
  }, [])

  const loadData = async () => {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }

    try {
      const [staffRes, patientsRes, tasksRes] = await Promise.all([
        axios.get(`${API_BASE}/staff/presence`, { headers }),
        axios.get(`${API_BASE}/patients`, { headers }),
        axios.get(`${API_BASE}/tasks`, { headers })
      ])
      setStaff(staffRes.data)
      setPatients(patientsRes.data)
      setTasks(tasksRes.data)
    } catch (err) {
      console.error('Failed to load data:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/')
  }

  if (!user) return <div>Loading...</div>

  return (
    <div style={{ minHeight: '100vh', padding: '2rem' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1>🏥 MediPresence Dashboard</h1>
          <div>
            <span style={{ marginRight: '1rem' }}>Welcome, {user.full_name} ({user.role})</span>
            <button className="btn btn-secondary" onClick={handleLogout}>Logout</button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
          {['status', 'patients', 'tasks'].map(tab => (
            <button
              key={tab}
              className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'status' && (
          <div className="card">
            <h2>Staff Status</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
              {staff.map((s: any) => (
                <div key={s.id} className="card" style={{ padding: '1rem' }}>
                  <h3>{s.full_name}</h3>
                  <p><strong>Role:</strong> {s.role}</p>
                  <p><strong>Status:</strong> {s.status}</p>
                  <p><strong>Activity:</strong> {s.activity}</p>
                  <p><strong>Location:</strong> {s.location}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'patients' && (
          <div className="card">
            <h2>Patients</h2>
            <div style={{ marginTop: '1rem' }}>
              {patients.map((p: any) => (
                <div key={p.id} className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
                  <h3>{p.name}</h3>
                  <p><strong>Age:</strong> {p.age} | <strong>Gender:</strong> {p.gender}</p>
                  <p><strong>Room:</strong> {p.room_number}</p>
                  <p><strong>Condition:</strong> {p.illness}</p>
                  <p><strong>Status:</strong> {p.status}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="card">
            <h2>Tasks</h2>
            <div style={{ marginTop: '1rem' }}>
              {tasks.map((t: any) => (
                <div key={t.id} className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
                  <h3>{t.title}</h3>
                  <p>{t.description}</p>
                  <p><strong>Priority:</strong> {t.priority} | <strong>Status:</strong> {t.status}</p>
                  {t.deadline && <p><strong>Deadline:</strong> {new Date(t.deadline).toLocaleDateString()}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

