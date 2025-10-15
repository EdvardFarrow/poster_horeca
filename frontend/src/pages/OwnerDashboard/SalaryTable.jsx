import React, { useEffect, useState } from "react";
import axios from "axios";
import SalaryDetailModal from "./SalaryDetailModal"; 

const API_URL = "http://localhost:8000";
const token = localStorage.getItem("access");
const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

export default function SalaryTable() {
    const [employees, setEmployees] = useState([]);
    const [month] = useState(10); 
    const [year] = useState(2025);
    const [days, setDays] = useState([]);
    const [salaries, setSalaries] = useState({}); 

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedSalaryData, setSelectedSalaryData] = useState(null);

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

    const fetchSalaries = async () => {
        try {
            const res = await axios.get(`${API_URL}/api/salary_records/?month=${month}&year=${year}`, axiosConfig);
            setSalaries(res.data);
        } catch (err) {
            console.error("Ошибка загрузки зарплат:", err);
        }
    };

    useEffect(() => {
        generateDays();
        fetchEmployees();
        fetchSalaries(); 
    }, [month, year]);

    const handleCellClick = (salaryData) => {
        if (salaryData) {
            setSelectedSalaryData(salaryData);
            setIsModalOpen(true);
        }
    };

    return (
        <>
            <div className="p-6">
                <h1 className="text-2xl font-semibold mb-4">Таблица зарплат за Октябрь {year}</h1>

                <div className="overflow-x-auto border rounded-lg">
                    <table className="min-w-full text-sm border-collapse">
                        <thead className="bg-gray-100">
                            <tr>
                                <th className="border p-2 text-left sticky left-0 bg-gray-100 z-10">Сотрудник</th>
                                {days.map((day) => (
                                    <th key={day} className="border p-2 text-center w-12">
                                        {day}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {employees.map((emp) => {
                                const empSalaries = salaries[emp.id] || {};
                                return (
                                    <tr key={emp.id} className="hover:bg-gray-50">
                                        <td className="border p-2 font-medium sticky left-0 bg-white hover:bg-gray-50 z-10">{emp.name}</td>
                                        {days.map((day) => {
                                            const salaryData = empSalaries[day];
                                            return (
                                                <td
                                                    key={day}
                                                    onClick={() => handleCellClick(salaryData)}
                                                    className={`border p-2 text-center ${
                                                        salaryData ? "bg-green-100 cursor-pointer hover:bg-green-200" : "bg-white"
                                                    }`}
                                                >
                                                    {salaryData ? Number(salaryData.total_salary).toFixed(0) : ""}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {isModalOpen && (
                <SalaryDetailModal
                    data={selectedSalaryData}
                    onClose={() => setIsModalOpen(false)}
            />
            )}
        </>
    );
}