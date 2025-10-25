import React from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { BarChart3, FileText, Users, Home, DollarSignIcon, UserCog } from "lucide-react";

const OwnerDashboard = () => {
    const location = useLocation();

    const getActiveTab = () => {
        const parts = location.pathname.split('/'); 
        return parts[2] || 'home';
    }
    const activeTab = getActiveTab();

    const navItems = [
        { id: "home", label: "Главная", icon: <Home size={18} /> },
        /* { id: "statistics", label: "Статистика", icon: <BarChart3 size={18} /> }, */
        { id: "reports", label: "Отчёты", icon: <FileText size={18} /> },
        { id: "employees", label: "Сотрудники", icon: <Users size={18} /> },
        { id: "salaries", label: "Зарплата", icon: <DollarSignIcon size={18} /> },
        { id: "roles", label: "Управл. ролями", icon: <UserCog size={18} /> },

    ];

    return (
        <div className="flex w-full min-h-screen">
            <div className="flex-none w-64 p-6 bg-gray-900 text-gray-200">
                <h1 className="text-3xl font-bold mb-6 text-white"></h1>
                <nav>
                    <ul>
                        {navItems.map((item) => (
                            <li key={item.id} className="mb-2">
                                <Link
                                    to={item.id === 'home' ? '/ownerdashboard' : `/ownerdashboard/${item.id}`}
                                    className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg transition-colors duration-200 ${
                                        activeTab === item.id
                                            ? "bg-blue-500 text-white shadow-md" 
                                            : "hover:bg-gray-700" 
                                    }`}
                                >
                                    {item.icon}
                                    <span className="font-medium">{item.label}</span>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </nav>
            </div>

            <div className="flex-grow bg-gray-100 dark:bg-gray-900 p-6 overflow-y-auto">
                
                <div className="border rounded-xl p-6 shadow bg-white text-gray-900 dark:bg-gray-800 dark:text-gray-100 min-h-full">
                    
                    {/* --- ВМЕСТО ВСЕХ {activeTab === "..."} СТАВИМ ОДИН <Outlet /> --- */}
                    {/* React Router сам вставит сюда нужный компонент (Salaries, Reports, etc.) */}
                    <Outlet />
                    
                </div>
            </div>
        </div>
    );
};

export default OwnerDashboard;