import axios from 'axios';

const API_URL = 'http://localhost:8000/api/auth/'; 

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

export async function login(username, password) {
    const { data } = await api.post('login/', { username, password });

    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    return data;
}

export async function register({ username, password, role = 'manager' }) {
    const { data } = await api.post('register/', { username, password, role });
    return data;
}

export function logout() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
}
