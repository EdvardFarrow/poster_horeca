import React, { useState, useEffect } from "react";
import api from "../../api"; 
import { HelpCircle } from "lucide-react";

export default function SalaryDetailModal({ data, onClose, onSaveSuccess }) {
    const [isEditing, setIsEditing] = useState(false);
    const [editableData, setEditableData] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [showBonusDetails, setShowBonusDetails] = useState(false); 

    useEffect(() => {
        if (data && data.details) {
            setEditableData({
                fixed: data.details.fixed || 0,
                percent: data.details.percent || 0,
                bonus: data.details.bonus || 0,
                write_off: data.details.write_off || 0,
                comment: data.details.comment || "",
            });
        }
    }, [data]);

    if (!data) return null;

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        let processedValue = value; 

        if (name !== "comment") {
            const numericValue = parseFloat(value);
            if (numericValue < 0) {
                processedValue = '0';
            }
        }
        
        setEditableData((prev) => ({
            ...prev,
            [name]: processedValue, 
        }));
    };

    const handleSave = async () => {
        setIsLoading(true);
        try {
            const payload = {
                details: {
                    fixed: parseFloat(editableData.fixed) || 0,
                    percent: parseFloat(editableData.percent) || 0,
                    bonus: parseFloat(editableData.bonus) || 0,
                    write_off: parseFloat(editableData.write_off) || 0,
                    comment: editableData.comment,
                }
            };
            
            const response = await api.patch(
                `/api/salary_records/${data.id}/`, 
                payload
            );

            onSaveSuccess(response.data); 
            setIsEditing(false);

        } catch (error) {
            console.error("Ошибка сохранения:", error.response?.data || error);
            alert("Не удалось сохранить изменения.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancel = () => {
        if (data && data.details) {
            setEditableData({
                fixed: data.details.fixed || 0,
                percent: data.details.percent || 0,
                bonus: data.details.bonus || 0,
                write_off: data.details.write_off || 0,
                comment: data.details.comment || "",
            });
        }
        setIsEditing(false);
    };

    const formatNumber = (num) => Number(num).toFixed(2);

    const calculatedTotal =
        (parseFloat(editableData.fixed) || 0) +
        (parseFloat(editableData.percent) || 0) +
        (parseFloat(editableData.bonus) || 0) -
        (parseFloat(editableData.write_off) || 0);

    const DetailRow = ({ label, value, name, isEditing }) => (
        <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 dark:text-gray-300">{label}:</span>
            {isEditing ? (
                <input
                    type="number"
                    name={name}
                    value={value}
                    onChange={handleInputChange}
                    className="font-medium text-right p-1 border rounded w-32 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                    step="0.01"
                    min="0"
                />
            ) : (
                <span className="font-medium text-gray-900 dark:text-gray-100">{formatNumber(value)} ₾</span>
            )}
        </div>
    );

    const hasBonusBreakdown = data?.details?.bonus_breakdown && data.details.bonus_breakdown.length > 0;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50" onClick={onClose}>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Детализация зарплаты</h2>
                <div className="space-y-1">
                    <DetailRow label="Фиксированная часть" value={editableData.fixed} name="fixed" isEditing={isEditing} />
                    <DetailRow label="Процент от продаж" value={editableData.percent} name="percent" isEditing={isEditing} />
                    
                    <div className="flex justify-between items-center py-1">
                        <div className="flex items-center gap-1.5 relative">
                            <span className="text-gray-600 dark:text-gray-300">Бонус за продукты:</span>
                            {hasBonusBreakdown && !isEditing && (
                                <>
                                    <HelpCircle 
                                        size={16} 
                                        className="text-blue-500 cursor-pointer" 
                                        onMouseEnter={() => setShowBonusDetails(true)}
                                        onMouseLeave={() => setShowBonusDetails(false)}
                                    />
                                    {showBonusDetails && (
                                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 bg-gray-900 text-white rounded-lg shadow-xl z-20">
                                            <h4 className="font-bold text-sm mb-1 border-b border-gray-700 pb-1">
                                                Детализация "банка" группы
                                            </h4>
                                            <div className="text-xs space-y-1 max-h-40 overflow-y-auto">
                                                <div className="grid grid-cols-5 gap-1 font-medium text-gray-400">
                                                    <span className="col-span-3">Продукт</span>
                                                    <span className="text-right">Кол-во</span>
                                                    <span className="text-right">Сумма</span>
                                                </div>
                                                {data.details.bonus_breakdown.map((item, index) => (
                                                    <div key={index} className="grid grid-cols-5 gap-1 items-center">
                                                        <span className="col-span-3 truncate">{item.product_name}</span>
                                                        <span className="text-right">{formatNumber(item.count)}</span>
                                                        <span className="text-right text-green-400">{formatNumber(item.total)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="text-xs italic text-gray-400 mt-2 pt-1 border-t border-gray-700">
                                                Ваша доля бонуса (<b>{formatNumber(editableData.bonus)} ₾</b>) — это часть от общего "банка".
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        {isEditing ? (
                            <input
                                type="number"
                                name="bonus"
                                value={editableData.bonus}
                                onChange={handleInputChange}
                                className="font-medium text-right p-1 border rounded w-32 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                                step="0.01"
                                min="0"
                            />
                        ) : (
                            <span className="font-medium text-gray-900 dark:text-gray-100">{formatNumber(editableData.bonus)} ₾</span>
                        )}
                    </div>

                    <DetailRow label="Списание" value={editableData.write_off} name="write_off" isEditing={isEditing} />

                    {isEditing ? (
                        <div className="pt-2">
                            <span className="text-gray-600 dark:text-gray-300">Комментарий:</span>
                            <textarea
                                name="comment"
                                value={editableData.comment}
                                onChange={handleInputChange}
                                className="w-full mt-1 p-1 border rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
                                rows="3"
                                placeholder="Причина списания или другой комментарий..."
                            />
                        </div>
                    ) : editableData.comment && (
                        <div className="pt-2 text-sm text-gray-500 border-t mt-2 dark:text-gray-400 dark:border-gray-700">
                            <strong className="text-gray-700 dark:text-gray-200">Комментарий:</strong> {editableData.comment}
                        </div>
                    )}

                    <hr className="my-2 border-gray-200 dark:border-gray-700" />
                    <div className="flex justify-between text-lg text-gray-900 dark:text-gray-100">
                        <span className="font-bold">Итого за смену:</span>
                        <span className="font-bold text-green-600 dark:text-green-400">{formatNumber(calculatedTotal)} ₾</span>
                    </div>
                </div>

                <div className="mt-6 flex justify-between items-center">
                    <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500 disabled:opacity-50" disabled={isLoading}>
                        Закрыть
                    </button>
                    {isEditing ? (
                        <div className="flex gap-2">
                            <button onClick={handleCancel} className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 dark:hover:bg-gray-400 disabled:opacity-50" disabled={isLoading}>
                                Отмена
                            </button>
                            <button onClick={handleSave} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 dark:hover:bg-blue-400 disabled:opacity-50" disabled={isLoading}>
                                {isLoading ? "Сохранение..." : "Сохранить"}
                            </button>
                        </div>
                    ) : (
                        <button onClick={() => setIsEditing(true)} className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 dark:hover:bg-yellow-400">
                            Редактировать
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}