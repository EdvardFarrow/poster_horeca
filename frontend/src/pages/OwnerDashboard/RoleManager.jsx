import React, { useState, useEffect } from 'react';
import api from '../../api'; 

export default function RoleManager() {
    const [roles, setRoles] = useState([]);
    const [payGroups, setPayGroups] = useState([]);

    const [editingRole, setEditingRole] = useState(null); 

    const fetchRoles = () => {
        api.get("/api/auth/role/")
        .then(res => setRoles(res.data))
        .catch(console.error);
    };

    const fetchPayGroups = () => {
        api.get("/api/auth/pay-group/") 
        .then(res => setPayGroups(res.data))
        .catch(console.error);
    };

    useEffect(() => {
        fetchRoles();
        fetchPayGroups();
    }, []);

    const handleEditClick = (role) => {
        setEditingRole({ ...role });
    };

    const handleGroupChange = (e) => {
        setEditingRole(prev => ({
        ...prev,
        pay_group: e.target.value ? Number(e.target.value) : null
        }));
    };

    const handleSubmit = () => {
        if (!editingRole) return;

        const payload = {
        name: editingRole.name,
        description: editingRole.description, 
        pay_group: editingRole.pay_group 
        };

        api.patch(`/api/auth/role/${editingRole.id}/`, payload)
        .then(() => {
            setEditingRole(null); 
            fetchRoles(); 
        })
        .catch(err => console.error("Ошибка сохранения:", err.response.data));
    };

    const handleCancel = () => {
        setEditingRole(null);
    };

    return (
        <div className="text-gray-900 dark:text-gray-100">
        <h2 className="text-2xl font-semibold mb-4">Управление Ролями и Группами</h2>

        {editingRole && (
            <div className="mb-4 p-4 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-2">
                Редактировать группу для: <span className="text-blue-400">{editingRole.name}</span>
            </h3>
            
            <label className="block mb-1 text-sm font-medium dark:text-gray-300">Группа расчета</label>
            <select
                value={editingRole.pay_group || ""}
                onChange={handleGroupChange}
                className="border p-2 rounded w-full bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
            >
                <option value="">Без группы</option>
                {payGroups.map(pg => (
                <option key={pg.id} value={pg.id}>{pg.name}</option>
                ))}
            </select>
            
            <div className="flex gap-2 mt-4">
                <button
                onClick={handleSubmit}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 dark:hover:bg-green-400"
                >
                Сохранить
                </button>
                <button
                onClick={handleCancel}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 dark:hover:bg-gray-400"
                >
                Отмена
                </button>
            </div>
            </div>
        )}

        <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700">
            <table className="w-full text-left">
            <thead className="border-b dark:border-gray-700">
                <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="p-2 font-semibold">Роль</th>
                <th className="p-2 font-semibold">Группа расчета (PayGroup)</th>
                <th className="p-2 font-semibold">Действия</th>
                </tr>
            </thead>
            <tbody>
                {roles.map(role => (
                <tr key={role.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900">
                    <td className="p-2">{role.name}</td>
                    <td className="p-2">
                        {role.pay_group_name ? (
                        <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">
                        {role.pay_group_name}
                        </span>
                    ) : (
                        <span className="text-gray-500">-</span>
                    )}
                    </td>
                    <td className="p-2">
                    <button
                        onClick={() => handleEditClick(role)}
                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                        title="Редактировать группу"
                    >
                        Изменить группу
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