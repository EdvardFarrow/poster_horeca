import { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

export const useAuth = () => {
    const [user, setUser] = useState(null);

    const login = async ({ username, password }) => {
        try {
        const { data } = await api.post('login/', { username, password });
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);
        setUser({ username }); // можно позже добавить роль/другие данные
        return data;
        } catch (err) {
        console.error('Login failed', err);
        throw err;
        }
    };

    const register = async ({ username, password }) => {
        try {
        const { data } = await api.post('register/', { username, password });
        return data;
        } catch (err) {
        console.error('Registration failed', err);
        throw err;
        }
    };

    const logout = () => {
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        setUser(null);
    };

    return { user, login, register, logout };
};
