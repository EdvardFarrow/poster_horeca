import React, { useMemo } from 'react';

const formatNumber = (num) => Number(num).toFixed(2);

const SummaryRow = ({ label, value, isNegative = false, isTotal = false }) => (
    <div className={`flex justify-between py-1 ${isTotal ? 'text-lg border-t-2 pt-2 dark:border-gray-700' : ''}`}> 
        <span className={isTotal ? "font-bold" : "text-gray-600 dark:text-gray-300"}>
            {label}:
        </span>
        <span className={`font-medium ${
            isTotal ? 'font-bold text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-gray-100'
        } ${
            isNegative ? 'text-red-600 dark:text-red-400' : ''
        }`}>
            {isNegative ? '-' : ''}{formatNumber(value)} ₾
        </span>
    </div>
);


export default function EmployeeMonthSummaryModal({ data, onClose }) {
    const { employee, salaryData } = data;

    const summary = useMemo(() => {
        let totalFixed = 0;
        let totalPercent = 0;
        let totalBonus = 0;
        let totalWriteOff = 0;
        let grandTotal = 0;
        
        const dailyRecords = Object.values(salaryData);
        const daysWorked = dailyRecords.length;

        for (const record of dailyRecords) {
            if (record && record.details) {
                totalFixed += parseFloat(record.details.fixed) || 0;
                totalPercent += parseFloat(record.details.percent) || 0;
                totalBonus += parseFloat(record.details.bonus) || 0;
                totalWriteOff += parseFloat(record.details.write_off) || 0;
            }
            grandTotal += parseFloat(record.total_salary) || 0;
        }

        return {
            daysWorked,
            totalFixed,
            totalPercent,
            totalBonus,
            totalWriteOff,
            grandTotal
        };
    }, [salaryData]); 

    if (!data) return null;

    return (
        <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50" 
            onClick={onClose}
        >
            <div 
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-sm" 
                onClick={(e) => e.stopPropagation()} 
            >
                <h2 className="text-xl font-bold mb-1 text-gray-900 dark:text-gray-100">Сводка за месяц</h2>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">{employee.name}</h3>

                <div className="space-y-1 text-gray-900 dark:text-gray-100">
                    <div className="flex justify-between pb-2">
                        <span className="text-gray-600 dark:text-gray-300">Отработано смен:</span>
                        <span className="font-medium">{summary.daysWorked}</span>
                    </div>

                    <SummaryRow label="Итого фикс. часть" value={summary.totalFixed} />
                    <SummaryRow label="Итого процент" value={summary.totalPercent} />
                    <SummaryRow label="Итого бонусы" value={summary.totalBonus} />
                    <SummaryRow label="Итого списания" value={summary.totalWriteOff} isNegative={true} />

                    <SummaryRow label="Итого к выплате" value={summary.grandTotal} isTotal={true} />
                </div>

                <div className="mt-6 flex justify-end">
                    <button 
                        onClick={onClose} 
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
                    >
                        Закрыть
                    </button>
                </div>
            </div>
        </div>
    );
}