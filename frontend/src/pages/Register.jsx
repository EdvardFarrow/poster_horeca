import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register as apiRegister } from '../api/auth'

export default function Register() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [role, setRole] = useState('manager')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const navigate = useNavigate()

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
        await apiRegister({ username, password, role })
        navigate('/login')
        } catch (err) {
        setError('Ошибка регистрации')
        } finally {
        setLoading(false)
        }
    }

    return (
        <div className="min-h-screen grid place-items-center bg-gray-100">
        <div className="w-full max-w-sm bg-white p-6 rounded-2xl shadow text-black">
            <h1 className="text-2xl font-semibold text-center">Регистрация</h1>
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
                <label className="block text-sm mb-1">Логин</label>
                <input
                className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                />
            </div>
            <div>
                <label className="block text-sm mb-1">Пароль</label>
                <input
                type="password"
                className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="new-password"
                />
            </div>
            <div>
                <label className="block text-sm mb-1">Роль</label>
                <select
                className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                value={role}
                onChange={e => setRole(e.target.value)}
                >
                <option value="manager">Менеджер</option>
                </select>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-60"
            >
                {loading ? 'Создаём…' : 'Зарегистрироваться'}
            </button>
            </form>
            <p className="text-center text-sm mt-4">
            Уже есть аккаунт? <Link to="/login" className="text-indigo-600 underline">Войти</Link>
            </p>
        </div>
        </div>
    )
}
