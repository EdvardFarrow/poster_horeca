import React, { useEffect, useState } from "react";
import api from "../../api";
import SalaryDetailModal from "./SalaryDetailModal";
import EmployeeMonthSummaryModal from "./EmployeeMonthSummaryModal"; 


export default function SalaryTable() {
    const [employees, setEmployees] = useState([]);
    
    const [currentDate, setCurrentDate] = useState(new Date());
    const [month, setMonth] = useState(currentDate.getMonth() + 1); 
    const [year, setYear] = useState(currentDate.getFullYear());
    
    const [days, setDays] = useState([]);
    const [salaries, setSalaries] = useState({});

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedSalaryData, setSelectedSalaryData] = useState(null);

    const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
    const [selectedEmployeeSummary, setSelectedEmployeeSummary] = useState(null); 

    const [isRecalculating, setIsRecalculating] = useState(false);


    
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

    const fetchSalaries = async () => {
        try {
            const res = await api.get(`/api/salary_records/?month=${month}&year=${year}`);
            setSalaries(res.data);
        } catch (err) {
            console.error("Ошибка загрузки зарплат:", err);
            setSalaries({}); 
        }
    };


    useEffect(() => {
        fetchEmployees();
    }, []);

    useEffect(() => {
        console.log(`Загрузка данных за ${month}/${year}`);
        generateDays();
        fetchSalaries();
    }, [month, year]); 



    const handleCellClick = (salaryData, employeeId, day) => {
        if (salaryData) {
            setSelectedSalaryData({ ...salaryData, employeeId, day });
            setIsModalOpen(true);
        }
    };

    const handleEmployeeClick = (employee, employeeSalaries) => {
        setSelectedEmployeeSummary({ employee, salaryData: employeeSalaries });
        setIsSummaryModalOpen(true);
    };

    const handleSaveSuccess = (updatedData) => {
        const { employeeId, day } = selectedSalaryData; 

        setSalaries(prevSalaries => {
            const newSalaries = JSON.parse(JSON.stringify(prevSalaries)); 
            
            if (newSalaries[employeeId] && newSalaries[employeeId][day]) {
                newSalaries[employeeId][day] = {
                    ...newSalaries[employeeId][day],
                    ...updatedData,
                };
            }
            return newSalaries;
        });

        setIsModalOpen(false); 
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
        return `Таблица зарплат за ${capitalizedMonthName} ${year}`;
    };


    const handleRecalculate = async () => {
        setIsRecalculating(true);
        console.log(`Запрос на пересчет ЗП за ${month}/${year}`);
        
        try {
            const response = await api.post(
                `/api/salary_records/recalculate/`, 
                { month, year }
            );
            
            console.log("Пересчет завершен:", response.data.message);

            await fetchSalaries(); 
            alert("Расчеты успешно обновлены!");

        } catch (err) {
            console.error("Ошибка при пересчете зарплат:", err);
            alert(`Ошибка при пересчете: ${err.response?.data?.error || err.message}`);
        } finally {
            setIsRecalculating(false);
        }
    };

    return (
        <>
            <div className="p-6 text-gray-900 dark:text-gray-100">

                <div className="flex justify-between items-center mb-4">
                    <h1 className="text-2xl font-semibold">{getFormattedHeader()}</h1>
                    <div className="flex gap-2">
                        <button
                            onClick={handleRecalculate}
                            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 dark:hover:bg-blue-400 disabled:opacity-50"
                            disabled={isRecalculating}
                        >
                            {isRecalculating ? "Пересчет..." : "Обновить расчеты"}
                        </button>

                        <button
                            onClick={() => handleChangeMonth(-1)}
                            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
                            disabled={isRecalculating}
                        >
                            &lt; Пред.
                        </button>
                        <button
                            onClick={() => handleChangeMonth(1)}
                            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
                            disabled={isRecalculating}
                        >
                            След. &gt;
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
                    <table className="min-w-full text-sm border-collapse">
                        <thead className="bg-gray-100 dark:bg-gray-700">
                            <tr className="border-b dark:border-gray-700">
                                <th className="border p-2 text-left sticky left-0 bg-gray-100 dark:bg-gray-700 z-10 font-semibold dark:border-gray-600">Сотрудник</th>
                                {days.map((day) => (
                                    <th key={day} className="border p-2 text-center w-12 font-semibold dark:border-gray-600">
                                        {day}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {employees.length > 0 ? employees.map((emp) => {
                                const empSalaries = salaries[emp.id] || {};
                                return (
                                    <tr key={emp.id} className="hover:bg-gray-50 dark:hover:bg-gray-900 border-t dark:border-gray-700">

                                        <td
                                            className="border p-2 font-medium sticky left-0 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 z-10 cursor-pointer dark:border-gray-600"
                                            onClick={() => handleEmployeeClick(emp, empSalaries)}
                                        >
                                            {emp.name}
                                        </td>

                                        {days.map((day) => {
                                            const salaryData = empSalaries[day];
                                            return (
                                                <td
                                                    key={day}
                                                    onClick={() => handleCellClick(salaryData, emp.id, day)}
                                                    className={`border p-2 text-center dark:border-gray-600 ${
                                                        salaryData
                                                        ? "bg-blue-100 text-blue-900 cursor-pointer hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-100 dark:hover:bg-blue-800" 
                                                        : "bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"                                                    
                                                    }`}
                                                >
                                                    {salaryData ? Number(salaryData.total_salary).toFixed(0) : ""}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                );
                            }) : (
                                <tr className="border-t dark:border-gray-700">
                                    <td colSpan={days.length + 1} className="text-center p-4 text-gray-500 dark:text-gray-400">Загрузка сотрудников...</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {isModalOpen && (
                <SalaryDetailModal
                    data={selectedSalaryData}
                    onClose={() => setIsModalOpen(false)}
                    onSaveSuccess={handleSaveSuccess}
                />
            )}

            {isSummaryModalOpen && (
                <EmployeeMonthSummaryModal
                    data={selectedEmployeeSummary}
                    onClose={() => setIsSummaryModalOpen(false)}
                />
            )}
        </>
    );
}