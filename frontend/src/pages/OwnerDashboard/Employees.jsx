import React, { useState, useEffect } from "react";
import api from "../../api";

export default function Employees() {
    const [employees, setEmployees] = useState([]);
    const [roles, setRoles] = useState([]);
    const [name, setName] = useState("");
    const [role, setRole] = useState("");

    
    const token = localStorage.getItem("access");

    

    useEffect(() => {
        if (!token) return;

        api
        .get("/api/auth/role/")
        .then((res) => setRoles(res.data))
        .catch((err) => console.error("Ошибка загрузки ролей:", err));

        api
        .get("/api/auth/employee/")
        .then((res) => setEmployees(res.data))
        .catch((err) => console.error("Ошибка загрузки сотрудников:", err));
    }, [token]);

    const addEmployee = () => {
        if (!name || !role) return;

        api
        .post("/api/auth/employee/", { name, role })
        .then((res) => {
            setEmployees([...employees, res.data]);
            setName("");
            setRole("");
        })
        .catch((err) => console.error("Ошибка добавления сотрудника:", err));
    };

    return (
    <div className="mb-8 text-gray-900 dark:text-gray-100">
        <h2 className="text-2xl font-semibold mb-4">Сотрудники</h2>

        {/* Form area */}
        <div className="flex flex-col sm:flex-row gap-2 mb-4 p-4 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
            <input
                type="text"
                placeholder="Имя сотрудника"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="border p-2 rounded flex-1 bg-white dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
            />
            <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="border p-2 rounded flex-1 bg-white dark:bg-gray-700 dark:border-gray-600"
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
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 dark:hover:bg-blue-400"
            >
                Добавить
            </button>
        </div>

        {/* Table area */}
        <div className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
            <table className="w-full text-center">
                <thead className="border-b dark:border-gray-700">
                    <tr className="bg-gray-100 dark:bg-gray-700">
                        <th className="p-2 font-semibold">Имя</th>
                        <th className="p-2 font-semibold">Роль</th>
                        <th className="p-2 font-semibold">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {employees.map((e) => (
                        <tr key={e.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900">
                            <td className="p-2">{e.name}</td>
                            <td className="p-2">{e.role_name || "-"}</td>
                            <td className="p-2">
                                <button
                                    onClick={() => handleDeleteEmployee(e.id)} 
                                    className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                    title="Удалить"
                                >
                                    Удалить
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);
}