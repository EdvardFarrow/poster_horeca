import { useState } from "react";
import SalaryRules from "./SalaryRules";
import SalaryTable from "./SalaryTable";
import SalarySchedule from "./SalarySchedule";

export default function Salaries() {
    const [activeTab, setActiveTab] = useState("salaryRules"); 

    return (
        <div className="flex w-full min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="p-6 bg-white dark:bg-gray-800 flex-none w-64 border-r border-gray-200 dark:border-gray-700">
            <h1 className="text-xl font-bold mb-6 text-gray-900 dark:text-gray-100">Зарплаты</h1>

            <nav className="text-gray-700 dark:text-gray-300">
            <ul>
                <li className="mb-2">
                <button
                    onClick={() => setActiveTab("salaryRules")}
                    className={`w-full text-left px-4 py-2 rounded transition-colors duration-200 ${
                    activeTab === "salaryRules"
                        ? "bg-blue-500 text-white"
                        : "hover:bg-gray-200 dark:hover:bg-gray-700"
                    }`}
                >
                    Формулы
                </button>
                </li>
                <li className="mb-2">
                <button
                    onClick={() => setActiveTab("salaryTable")}
                    className={`w-full text-left px-4 py-2 rounded transition-colors duration-200 ${
                    activeTab === "salaryTable"
                        ? "bg-blue-500 text-white"
                        : "hover:bg-gray-200 dark:hover:bg-gray-700"
                    }`}
                >
                    Таблица зарплат
                </button>
                </li>
                <li className="mb-2">
                <button
                    onClick={() => setActiveTab("salarySchedule")}
                    className={`w-full text-left px-4 py-2 rounded transition-colors duration-200 ${
                    activeTab === "salarySchedule"
                        ? "bg-blue-500 text-white"
                        : "hover:bg-gray-200 dark:hover:bg-gray-700"
                    }`}
                >
                    График смен
                </button>
                </li>
            </ul>
            </nav>
        </div>

        <div className="flex-grow p-6 overflow-y-auto">
            {activeTab === "salaryRules" && <SalaryRules />}
            {activeTab === "salaryTable" && <SalaryTable />}
            {activeTab === "salarySchedule" && <SalarySchedule />}
        </div>
        </div>
    );
}