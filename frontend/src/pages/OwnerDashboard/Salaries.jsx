import { useState } from "react";
import SalaryRules from "./SalaryRules";
import SalaryTable from "./SalaryTable";
import SalarySchedule from "./SalarySchedule";

export default function Salaries() {
    const [activeTab, setActiveTab] = useState("salaryRules"); 

    return (
        <div className="flex w-full min-h-screen">
        <div className="p-6 bg-gray-50 flex-none w-64 border-r border-gray-200">
            <h1 className="text-3xl font-bold mb-6">Зарплаты</h1>

            <nav>
            <ul>
                <li className="mb-2">
                <button
                    onClick={() => setActiveTab("salaryRules")}
                    className={`w-full text-left px-4 py-2 rounded transition-colors duration-200 ${
                    activeTab === "salaryRules"
                        ? "bg-blue-500 text-white"
                        : "hover:bg-gray-200"
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
                        : "hover:bg-gray-200"
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
                        : "hover:bg-gray-200"
                    }`}
                >
                    График смен
                </button>
                </li>
            </ul>
            </nav>
        </div>

        <div className="flex-grow p-6 bg-white overflow-y-auto">
            {activeTab === "salaryRules" && <SalaryRules />}
            {activeTab === "salaryTable" && <SalaryTable />}
            {activeTab === "salarySchedule" && <SalarySchedule />}
        </div>
        </div>
    );
}