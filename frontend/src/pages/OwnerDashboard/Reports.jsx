import { useState } from "react";
import CashShifts from "./CashShifts";
import ShiftSales from "./ShiftSales";

export default function Reports() {
  const [activeTab, setActiveTab] = useState("cashShifts"); // cashShifts | shiftSales

    return (
        <div className="flex w-full min-h-screen">
        {/* Левая боковая панель для навигации */}
        <div className="p-6 bg-gray-50 flex-none w-64 border-r border-gray-200">
            <h1 className="text-3xl font-bold mb-6">Отчёты</h1>

            <nav>
            <ul>
                <li className="mb-2">
                <button
                    onClick={() => setActiveTab("cashShifts")}
                    className={`w-full text-left px-4 py-2 rounded transition-colors duration-200 ${
                    activeTab === "cashShifts"
                        ? "bg-blue-500 text-white"
                        : "hover:bg-gray-200"
                    }`}
                >
                    Кассовые смены
                </button>
                </li>
                <li className="mb-2">
                <button
                    onClick={() => setActiveTab("shiftSales")}
                    className={`w-full text-left px-4 py-2 rounded transition-colors duration-200 ${
                    activeTab === "shiftSales"
                        ? "bg-blue-500 text-white"
                        : "hover:bg-gray-200"
                    }`}
                >
                    Продажи по сменам
                </button>
                </li>
            </ul>
            </nav>
        </div>

        {/* Правая область для контента, скроллится при необходимости */}
        <div className="flex-grow p-6 bg-white overflow-y-auto">
            {activeTab === "cashShifts" && <CashShifts />}
            {activeTab === "shiftSales" && <ShiftSales />}
        </div>
        </div>
    );
}