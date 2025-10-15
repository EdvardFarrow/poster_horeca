import React, { useState, useEffect } from "react";
import axios from "axios";

export default function Employees() {
    const [employees, setEmployees] = useState([]);
    const [roles, setRoles] = useState([]);
    const [name, setName] = useState("");
    const [role, setRole] = useState("");

    // Берем токен из localStorage (или откуда сохраняешь после логина)
    const token = localStorage.getItem("access");

    const axiosConfig = {
        headers: {
        Authorization: `Bearer ${token}`,
        },
    };

    // Загружаем роли и сотрудников с API
    useEffect(() => {
        if (!token) return;

        axios
        .get("/api/auth/role/", axiosConfig)
        .then((res) => setRoles(res.data))
        .catch((err) => console.error("Ошибка загрузки ролей:", err));

        axios
        .get("/api/auth/employee/", axiosConfig)
        .then((res) => setEmployees(res.data))
        .catch((err) => console.error("Ошибка загрузки сотрудников:", err));
    }, [token]);

    const addEmployee = () => {
        if (!name || !role) return;

        axios
        .post("/api/auth/employee/", { name, role }, axiosConfig)
        .then((res) => {
            setEmployees([...employees, res.data]);
            setName("");
            setRole("");
        })
        .catch((err) => console.error("Ошибка добавления сотрудника:", err));
    };

    return (
        <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Сотрудники</h2>

        {/* Форма добавления сотрудника */}
        <div className="flex gap-2 mb-4">
            <input
            type="text"
            placeholder="Имя сотрудника"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="border p-2 rounded flex-1"
            />
            <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="border p-2 rounded flex-1"
            >
            <option value="">Выберите роль</option>
            {roles.map((r) => (
                <option key={r.id} value={r.id}>
                {r.name}
                </option>
            ))}
            </select>
            <button
            onClick={addEmployee}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
            Добавить
            </button>
        </div>

        {/* Таблица сотрудников */}
        <table className="w-full border border-gray-300">
            <thead>
            <tr className="bg-gray-200">
                <th className="p-2">Имя</th>
                <th className="p-2">Роль</th>
            </tr>
            </thead>
            <tbody>
            {employees.map((e) => (
                <tr key={e.id} className="border-t border-gray-300">
                <td className="p-2">{e.name}</td>
                <td className="p-2">{e.role_name || ""}</td>
                </tr>
            ))}
            </tbody>
        </table>
        </div>
    );
}
