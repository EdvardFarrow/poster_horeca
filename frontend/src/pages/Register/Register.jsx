import React from 'react';

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register as apiRegister } from '../../api/auth'

export default function Register() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [fullname, setFullname] = useState('');
    const [error, setError] = useState('')
    const navigate = useNavigate()
    const validateFullname = (name) => {
        return name.split(' ').every(word => /^[A-ZА-ЯЁ][a-zа-яё]+$/.test(word));
    };

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError('')

        if (!validateFullname(fullname)) {
            setError('Имя и фамилия должны начинаться с заглавной буквы')
            setLoading(false)
            return
        }

        try {
            await apiRegister({ 
                username: username.trim(), 
                password, 
                fullname: fullname.trim(), 
                role: 'employee'  
            })
            navigate('/login')
        } catch (err) {
            if (err.response?.data?.detail) {
                setError(err.response.data.detail)
            } else {
                setError('Ошибка регистрации')
            }
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
                autoComplete="new-password"
                />
            </div>
            <div>
                <label htmlFor="fullname" className="block text-sm mb-1">Имя и Фамилия</label>
                <input
                id="fullname"
                className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                value={fullname}
                onChange={e => setFullname(e.target.value)}
                autoComplete="name"
                />
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
