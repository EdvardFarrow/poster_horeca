import React from "react";

export default function SalaryDetailModal({ data, onClose }) {
    if (!data) return null;

    const formatNumber = (num) => Number(num).toFixed(2);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50" onClick={onClose}>
        <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">Детализация зарплаты</h2>
            <div className="space-y-2">
            <div className="flex justify-between">
                <span className="text-gray-600">Фиксированная часть:</span>
                <span className="font-medium">{formatNumber(data.details.fixed)} ₽</span>
            </div>
            <div className="flex justify-between">
                <span className="text-gray-600">Процент от продаж:</span>
                <span className="font-medium">{formatNumber(data.details.percent)} ₽</span>
            </div>
            <div className="flex justify-between">
                <span className="text-gray-600">Бонус за продукты:</span>
                <span className="font-medium">{formatNumber(data.details.bonus)} ₽</span>
            </div>
            <hr className="my-2" />
            <div className="flex justify-between text-lg">
                <span className="font-bold">Итого за смену:</span>
                <span className="font-bold text-green-600">{formatNumber(data.total_salary)} ₽</span>
            </div>
            </div>
            <div className="mt-6 flex justify-end">
            <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
                Закрыть
            </button>
            </div>
        </div>
        </div>
    );
    }