import api from '../api'; 

export const login = async (username, password) => {
    try {
        const response = await api.post('/api/auth/token/', {
        username,
        password,
        });
        
        localStorage.setItem('access', response.data.access);
        localStorage.setItem('refresh', response.data.refresh);
        
        return response.data; 

    } catch (error) {
        console.error('Login failed:', error);
        throw error; 
    }
    };

    export const getUserInfo = async () => {
    try {
        const response = await api.get('/api/auth/user/'); 
        
        return response.data; 

    } catch (error) {
        console.error('Failed to get user info:', error);
        throw error;
    }
};

export const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    window.location.href = '/login';
}