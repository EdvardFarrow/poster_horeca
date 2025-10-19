import React, { useEffect, useState } from "react";
import api from "../../api";

export default function ShiftTable() {
    const [employees, setEmployees] = useState([]);
    
    const [currentDate, setCurrentDate] = useState(new Date());
    const [month, setMonth] = useState(currentDate.getMonth() + 1);
    const [year, setYear] = useState(currentDate.getFullYear());
    
    const [days, setDays] = useState([]);
    const [shifts, setShifts] = useState({});

    const fetchEmployees = async () => {
        try {
            const res = await api.get(`/api/auth/employee/`);
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
            const res = await api.get(`/api/shifts/?month=${month}&year=${year}`);
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
            setShifts({}); 
        }
    };
    
    useEffect(() => {
        fetchEmployees(); 
    }, []);

    useEffect(() => {
        generateDays();
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
            await api.post(`/api/shifts/save_month/`, { shifts: payload });
            alert("Смены сохранены!");
        } catch (err) {
            console.error("Ошибка сохранения смен:", err);
            alert("Ошибка сохранения!");
        }
    };

    const handleChangeMonth = (offset) => {
        const newDate = new Date(year, month - 1, 1);
        newDate.setMonth(newDate.getMonth() + offset);
        setMonth(newDate.getMonth() + 1);
        setYear(newDate.getFullYear());
    };

    const getFormattedHeader = () => {
        const d = new Date(year, month - 1);
        const monthName = d.toLocaleString('default', { month: 'long' });
        const capitalizedMonthName = monthName.charAt(0).toUpperCase() + monthName.slice(1);
        return `Смены за ${capitalizedMonthName} ${year}`;
    };

    return (
        <div className="text-gray-900 dark:text-gray-100">
        
        <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-semibold">{getFormattedHeader()}</h1>
            <div className="flex gap-2">
                <button 
                    onClick={() => handleChangeMonth(-1)} 
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                >
                    &lt; Пред.
                </button>
                <button 
                    onClick={() => handleChangeMonth(1)} 
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                >
                    След. &gt;
                </button>
            </div>
        </div>

        <div className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
            <table className="min-w-full text-sm border-collapse">
            <thead className="bg-gray-100 dark:bg-gray-700">
                <tr className="border-b dark:border-gray-700">
                <th className="border p-2 text-left font-semibold dark:border-gray-600">Сотрудник</th>
                {days.map((day) => (
                    <th key={day} className="border p-2 text-center w-10 font-semibold dark:border-gray-600">
                    {day}
                    </th>
                ))}
                </tr>
            </thead>
            <tbody>
                {employees.map((emp) => (
                <tr key={emp.id} className="dark:hover:bg-gray-900">
                    <td className="border p-2 font-medium dark:border-gray-600">{emp.name}</td>
                    {days.map((day) => (
                    <td
                        key={day}
                        onClick={() => toggleShift(emp.id, day)}
                        className={`border p-2 text-center cursor-pointer select-none dark:border-gray-600 ${
                        shifts[emp.id]?.[day] 
                            ? "bg-green-400 text-gray-900" 
                            : "bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
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
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-500"
                >
                Сохранить изменения
            </button>
        </div>
        </div>
    );
}