import axios from "axios";

const API_URL = "http://localhost:8000";

const api = axios.create({
    baseURL: API_URL,
    });

    api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access");
        if (token) {
        config.headers["Authorization"] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
    );


    api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        if (error.response.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
            const refreshToken = localStorage.getItem("refresh");
            
            const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
            refresh: refreshToken,
            });

            const { access } = response.data;
            localStorage.setItem("access", access);
            
            if (response.data.refresh) {
                localStorage.setItem("refresh", response.data.refresh);
            }

            api.defaults.headers.common["Authorization"] = `Bearer ${access}`;
            originalRequest.headers["Authorization"] = `Bearer ${access}`;

            return api(originalRequest);

        } catch (refreshError) {
            console.error("Refresh token is invalid, logging out.", refreshError);
            localStorage.removeItem("access");
            localStorage.removeItem("refresh");
            window.location.href = '/login'; 
            
            return Promise.reject(refreshError);
        }
        }

        return Promise.reject(error);
    }
);

export default api;