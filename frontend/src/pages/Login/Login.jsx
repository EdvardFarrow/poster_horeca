import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login, getUserInfo } from '../../api/auth'

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const navigate = useNavigate()

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
            await login(username.trim(), password)

            const user = await getUserInfo() 

            switch (user.role) {
                case 'manager':
                    navigate('/manager')
                    break
                case 'owner':
                    navigate('/ownerdashboard') 
                    break
                default:
                    navigate('/employee')
            }
        } catch (err) {
            setError('Неверный логин или пароль')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen grid place-items-center bg-gray-100">
            <div className="w-full max-w-sm bg-white text-black p-6 rounded-2xl shadow">
                <h1 className="text-2xl font-semibold text-center">Вход</h1>
                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <div>
                        <label htmlFor="username" className="block text-sm mb-1">Логин</label>
                        <input
                        id="username"
                        className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        autoComplete="username"
                        />
                    </div>
                    <div>
                        <label htmlFor="password" className="block text-sm mb-1">Пароль</label>
                        <input
                        id="password"
                        type="password"
                        className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        autoComplete="current-password"
                        />
                    </div>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-60"
                    >
                        {loading ? 'Входим…' : 'Войти'}
                    </button>
                </form>
                <p className="text-center text-sm mt-4">
                    {/*Нет аккаунта? <Link to="/register" className="text-indigo-600 underline">Зарегистрироваться</Link> */}
                </p>
            </div>
        </div>
    )
}
