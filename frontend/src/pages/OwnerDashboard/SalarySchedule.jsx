import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";
const token = localStorage.getItem("access");
const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

export default function ShiftTable() {
    const [employees, setEmployees] = useState([]);
    const [month] = useState(10);
    const [year] = useState(2025);
    const [days, setDays] = useState([]);
    const [shifts, setShifts] = useState({});

    const fetchEmployees = async () => {
        try {
            const res = await axios.get(`${API_URL}/api/auth/employee/`, axiosConfig);
            setEmployees(res.data);
        } catch (err) {
            console.error("Ошибка загрузки сотрудников:", err);
        }
    };

    const generateDays = () => {
        const daysInMonth = new Date(year, month, 0).getDate();
        const dayArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);
        setDays(dayArray);
    };

    const fetchShifts = async () => {
        try {
            const res = await axios.get(`${API_URL}/api/shifts/?month=${month}&year=${year}`, axiosConfig);
            const loadedShifts = {};

            res.data.forEach(({ date, employees }) => {
                const day = Number(date.split("-")[2]);
                employees.forEach((empId) => {
                    if (!loadedShifts[empId]) loadedShifts[empId] = {};
                    loadedShifts[empId][day] = true;
                });
            });

            setShifts(loadedShifts);
        } catch (err) {
            console.error("Ошибка загрузки смен:", err);
        }
    };

    useEffect(() => {
        generateDays();
        fetchEmployees(); 
        fetchShifts(); 
    }, [month, year]);


    const toggleShift = (empId, day) => {
        setShifts((prev) => ({
            ...prev,
            [empId]: {
                ...prev[empId],
                [day]: !prev[empId]?.[day],
            },
        }));
    };

    const saveShifts = async () => {
        const payloadMap = {};

        Object.entries(shifts).forEach(([empId, daysWorked]) => {
            Object.entries(daysWorked).forEach(([day, worked]) => {
                if (worked) {
                    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                    if (!payloadMap[date]) payloadMap[date] = [];
                    payloadMap[date].push(Number(empId));
                }
            });
        });

        const payload = Object.entries(payloadMap).map(([date, employees]) => ({ date, employees }));

        try {
            await axios.post(`${API_URL}/api/shifts/save_month/`, { shifts: payload }, axiosConfig);
            alert("Смены сохранены!");
        } catch (err) {
            console.error("Ошибка сохранения смен:", err);
            alert("Ошибка сохранения!");
        }
    };

    return (
        <div className="p-6">
        <h1 className="text-2xl font-semibold mb-4">Смены за Октябрь {year}</h1>

        <div className="overflow-x-auto border rounded-lg">
            <table className="min-w-full text-sm border-collapse">
            <thead className="bg-gray-100">
                <tr>
                <th className="border p-2">Сотрудник</th>
                {days.map((day) => (
                    <th key={day} className="border p-2 text-center w-10">
                    {day}
                    </th>
                ))}
                </tr>
            </thead>
            <tbody>
                {employees.map((emp) => (
                <tr key={emp.id}>
                    <td className="border p-2 font-medium">{emp.name}</td>
                    {days.map((day) => (
                    <td
                        key={day}
                        onClick={() => toggleShift(emp.id, day)}
                        className={`border p-2 text-center cursor-pointer select-none ${
                        shifts[emp.id]?.[day] ? "bg-green-400" : "bg-white hover:bg-gray-100"
                        }`}
                    >
                        {shifts[emp.id]?.[day] ? "✓" : ""}
                    </td>
                    ))}
                </tr>
                ))}
            </tbody>
            </table>
        </div>

        <div className="mt-4 flex justify-end">
            <button
                onClick={saveShifts}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                Сохранить изменения
            </button>
        </div>
        </div>
    );
}