import axios from 'axios';

const API_URL = 'http://localhost:8000/api/auth/'; 

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

export async function register({ username, password, fullname, role = 'employee' }) {
    const { data } = await api.post('register/', { username, password, fullname, role });
    return data;
}


export async function login(username, password) {
    const { data } = await api.post('login/', { username, password });

    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    return data;
}

export async function registerAndLogin({ username, password, fullname, role = 'employee' }) {
    await register({ username, password, fullname, role }); 
    return await login(username, password); 
}

export function logout() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
}

export async function getUserInfo() {
    const token = localStorage.getItem('access');
    if (!token) return null;

    const { data } = await api.get('me/', {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    return data;
}
