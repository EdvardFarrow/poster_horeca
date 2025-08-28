import React, { useState } from "react";
import Analytics from "./Analytics";
import Reports from "./Reports";
import Salaries from "./Salaries";

const OwnerDashboard = () => {
    const [activeTab, setActiveTab] = useState("analytics");

    const renderContent = () => {
        switch (activeTab) {
        case "analytics":
            return <Analytics />;
        case "reports":
            return <Reports />;
        case "salaries":
            return <Salaries />;
        default:
            return <Analytics />;
        }
    };

    return (
        <div className="flex">
        {/* Sidebar */}
        <div className="w-48 border-r p-4">
            <h2 className="font-bold mb-4">Меню</h2>
            <ul>
            <li
                className={`cursor-pointer mb-2 ${
                activeTab === "analytics" ? "font-bold" : ""
                }`}
                onClick={() => setActiveTab("analytics")}
            >
                Аналитика
            </li>
            <li
                className={`cursor-pointer mb-2 ${
                activeTab === "reports" ? "font-bold" : ""
                }`}
                onClick={() => setActiveTab("reports")}
            >
                Отчёты
            </li>
            <li
                className={`cursor-pointer ${
                activeTab === "salaries" ? "font-bold" : ""
                }`}
                onClick={() => setActiveTab("salaries")}
            >
                Зарплаты
            </li>
            </ul>
        </div>

        {/* Основной контент */}
        <div className="flex-1 p-4">{renderContent()}</div>
        </div>
    );
    };

export default OwnerDashboard;
