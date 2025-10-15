import React, { useState } from "react";
import Statistics from "./Statistics";
import Reports from "./Reports"; 
import Employees from "./Employees";
import Salaries from "./Salaries";
import { BarChart3, FileText, Users, Home, DollarSignIcon } from "lucide-react";

const OwnerDashboard = () => {
    const [activeTab, setActiveTab] = useState("home");

    const navItems = [
        { id: "home", label: "Главная", icon: <Home size={18} /> },
        { id: "statistics", label: "Статистика", icon: <BarChart3 size={18} /> },
        { id: "reports", label: "Отчёты", icon: <FileText size={18} /> },
        { id: "employees", label: "Сотрудники", icon: <Users size={18} /> },
        { id: "salaries", label: "Зарплата", icon: <DollarSignIcon size={18} /> },
    ];

    return (
        <div className="flex w-full min-h-screen">
            {/* Левая боковая панель для навигации */}
            <div className="flex-none w-64 p-6 bg-gray-900 text-gray-200">
                <h1 className="text-3xl font-bold mb-6 text-white"></h1>
                <nav>
                    <ul>
                        {navItems.map((item) => (
                            <li key={item.id} className="mb-2">
                                <button
                                    onClick={() => setActiveTab(item.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg transition-colors duration-200 ${
                                        activeTab === item.id
                                            ? "bg-blue-500 text-white shadow-md"
                                            : "hover:bg-gray-700"
                                    }`}
                                >
                                    {item.icon}
                                    <span className="font-medium">{item.label}</span>
                                </button>
                            </li>
                        ))}
                    </ul>
                </nav>
            </div>

            {/* Правая область для контента с прокруткой */}
            <div className="flex-grow bg-gray-100 p-6 overflow-y-auto">
                <div className="border rounded-xl p-6 shadow bg-white min-h-full">
                    {activeTab === "home" && (
                        <div>
                            <p className="text-lg mb-4">Добро пожаловать в панель владельца!</p>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 flex-grow">
                                    <h2 className="text-sm text-gray-500">Выручка (сегодня)</h2>
                                    <p className="text-xl font-semibold">₽ 125,000</p>
                                </div>
                                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 flex-grow">
                                    <h2 className="text-sm text-gray-500">Расходы (сегодня)</h2>
                                    <p className="text-xl font-semibold">₽ 52,000</p>
                                </div>
                                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 flex-grow">
                                    <h2 className="text-sm text-gray-500">Сотрудники</h2>
                                    <p className="text-xl font-semibold">12</p>
                                </div>
                                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 flex-grow">
                                    <h2 className="text-sm text-gray-500">Зарплата</h2>
                                    <p className="text-xl font-semibold">12</p>
                                </div>
                            </div>
                        </div>
                    )}
                    {activeTab === "statistics" && <Statistics />}
                    {activeTab === "reports" && <Reports />}
                    {activeTab === "employees" && <Employees />}
                    {activeTab === "salaries" && <Salaries />}
                </div>
            </div>
        </div>
    );
};

export default OwnerDashboard;