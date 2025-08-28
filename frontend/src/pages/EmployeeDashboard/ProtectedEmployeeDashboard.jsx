import { useState, useEffect } from "react";
import { Navigate } from "react-router-dom";
import EmployeeDashboard from "./EmployeeDashboard";
import { getUserInfo } from "../../api/auth";

export default function ProtectedEmployeeDashboard() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchUser() {
        try {
            const data = await getUserInfo();
            setUser(data);
        } catch (err) {
            console.error("Ошибка при получении пользователя:", err);
            setUser(null);
        } finally {
            setLoading(false);
        }
        }
        fetchUser();
    }, []);

    if (loading) {
        return (
        <div className="min-h-screen grid place-items-center bg-gray-50">
            <p className="text-gray-500 text-lg">Загрузка...</p>
        </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <EmployeeDashboard user={user} />;
}
