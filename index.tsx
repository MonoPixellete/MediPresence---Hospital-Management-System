import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

export default function Home() {
  const router = useRouter()
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
    role: 'staff'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isLogin ? '/login' : '/register'
      const response = await axios.post(`${API_BASE}${endpoint}`, formData)
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token)
        localStorage.setItem('user', JSON.stringify(response.data))
        router.push('/dashboard')
      } else {
        setError(isLogin ? 'Invalid credentials' : 'Registration failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ maxWidth: '400px', width: '100%' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>🏥 MediPresence</h1>
        
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
          <button
            className={`btn ${isLogin ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setIsLogin(true)}
            style={{ flex: 1 }}
          >
            Login
          </button>
          <button
            className={`btn ${!isLogin ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setIsLogin(false)}
            style={{ flex: 1 }}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <input
                className="input"
                type="text"
                placeholder="Full Name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
                style={{ marginBottom: '1rem' }}
              />
              <input
                className="input"
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                style={{ marginBottom: '1rem' }}
              />
              <select
                className="input"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                style={{ marginBottom: '1rem' }}
              >
                <option value="staff">Staff</option>
                <option value="doctor">Doctor</option>
                <option value="nurse">Nurse</option>
                <option value="receptionist">Receptionist</option>
                <option value="admin">Admin</option>
              </select>
            </>
          )}
          
          <input
            className="input"
            type="text"
            placeholder="Username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            required
            style={{ marginBottom: '1rem' }}
          />
          <input
            className="input"
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
            style={{ marginBottom: '1rem' }}
          />

          {error && (
            <div style={{ color: 'red', marginBottom: '1rem', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>
      </div>
    </div>
  )
}

