import React from 'react';

export default function DashboardHome() {
    return (
        <div>
            <p className="text-lg mb-4">Добро пожаловать в панель владельца!</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                
                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 dark:bg-gray-700 flex-grow">
                    <h2 className="text-sm text-gray-500 dark:text-gray-400">Выручка (вчера)</h2>
                    <p className="text-xl font-semibold"></p>
                </div>
                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 dark:bg-gray-700 flex-grow">
                    <h2 className="text-sm text-gray-500 dark:text-gray-400">Расходы (вчера)</h2>
                    <p className="text-xl font-semibold"></p>
                </div>
                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 dark:bg-gray-700 flex-grow">
                    <h2 className="text-sm text-gray-500 dark:text-gray-400">Сотрудники</h2>
                    <p className="text-xl font-semibold"></p>
                </div>
                <div className="p-4 border rounded-lg shadow-sm bg-gray-50 dark:bg-gray-700 flex-grow">
                    <h2 className="text-sm text-gray-500 dark:text-gray-400">Зарплата</h2>
                    <p className="text-xl font-semibold"></p>
                </div>
            </div>
        </div>
    );
}