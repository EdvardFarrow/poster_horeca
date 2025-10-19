import { useState, useEffect } from "react";
import { getCashShifts } from "../../api/poster";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

export default function CashShifts() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [dateFrom, setDateFrom] = useState(null);
    const [dateTo, setDateTo] = useState(null);
    const [spotId, setSpotId] = useState(1);

    const [totals, setTotals] = useState({
        revenue: 0,
        cash: 0,
        card: 0,
        credit: 0,
        collection: 0,
    });

    useEffect(() => {
        fetchData();
    }, [dateFrom, dateTo, spotId]);

    const fetchData = async () => {
        setLoading(true);
        try {
        const rawData = await getCashShifts({ dateFrom, dateTo, spot_id: spotId });

        const sortedForTable = [...rawData].sort(
            (a, b) => new Date(b.timestart) - new Date(a.timestart)
        );

        setData(sortedForTable);

        const totals = rawData.reduce(
            (acc, item) => {
            acc.revenue += (item.amount_sell_cash || 0) + (item.amount_sell_card || 0);
            acc.cash += item.amount_sell_cash || 0;
            acc.card += item.amount_sell_card || 0;
            acc.credit += item.amount_credit || 0;
            acc.collection += item.amount_collection || 0;
            return acc;
            },
            { revenue: 0, cash: 0, card: 0, credit: 0, collection: 0 }
        );
        setTotals(totals);
        } catch (err) {
        console.error("Ошибка получения кассовых смен:", err);
        setData([]);
        setTotals({ revenue: 0, cash: 0, card: 0, credit: 0, collection: 0 });
        } finally {
        setLoading(false);
        }
    };

    const renderTable = () => {
        if (!data || data.length === 0) return <div>Нет данных</div>;

        const headers = [
        "timestart",
        "timeend",
        "amount_start",
        "amount_end",
        "amount_sell_cash",
        "amount_sell_card",
        "revenue_total",
        "amount_credit",
        "amount_collection",
        ];

        const headerLabels = {
        timestart: "Начало смены",
        timeend: "Конец смены",
        amount_start: "Сумма в начале",
        amount_end: "Сумма в конце",
        amount_sell_cash: "Выручка наличными",
        amount_sell_card: "Выручка картой",
        revenue_total: "Общая выручка",
        amount_credit: "Расходы",
        amount_collection: "Инкассация",
        };

        const formatDate = (d) =>
        d && d !== "0000-00-00 00:00:00" ? new Date(d).toLocaleString() : "";

        return (
            <div className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-100 dark:bg-gray-700">
                        <tr className="border-b dark:border-gray-700">
                            {headers.map((h) => (
                                <th key={h} className="px-4 py-2 border dark:border-gray-600 font-semibold text-left">
                                    {headerLabels[h]}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row, idx) => (
                            <tr key={idx} className="border-t dark:border-gray-700 odd:bg-white even:bg-gray-50 dark:odd:bg-gray-800 dark:even:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600">
                                <td className="px-4 py-2 border dark:border-gray-600">{formatDate(row.timestart)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600">{formatDate(row.timeend)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{(row.amount_start || 0).toFixed(2)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{(row.amount_end || 0).toFixed(2)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{(row.amount_sell_cash || 0).toFixed(2)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{(row.amount_sell_card || 0).toFixed(2)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{((row.amount_sell_cash || 0) + (row.amount_sell_card || 0)).toFixed(2)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{(row.amount_credit || 0).toFixed(2)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-right">{(row.amount_collection || 0).toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    return (
        <div className="text-gray-900 dark:text-gray-100">
        {/* Фильтр по датам */}
        <div className="mb-4 flex gap-2 items-center flex-wrap">
            <span className="dark:text-gray-300">С:</span>
            <DatePicker
                selected={dateFrom}
                onChange={setDateFrom}
                dateFormat="yyyy-MM-dd"
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
            />
            <span className="dark:text-gray-300">По:</span>
            <DatePicker
                selected={dateTo}
                onChange={setDateTo}
                dateFormat="yyyy-MM-dd"
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
            />
            <button
                onClick={() => {
                    setDateFrom(null);
                    setDateTo(null);
                }}
                className="bg-gray-300 text-gray-800 px-2 py-1 rounded hover:bg-gray-400 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
            >
                Сбросить
            </button>
            <select
                value={spotId}
                onChange={e => setSpotId(Number(e.target.value))}
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
            >
                <option value={1}>Ресторан</option>
                <option value={2}>Доставка</option>
            </select>
        </div>

        {/* Итоги */}
        <div className="mb-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:border dark:border-gray-700">
                <div className="text-gray-500 dark:text-gray-400">Общая выручка</div>
                <div className="text-xl font-bold">{totals.revenue.toFixed(2)}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:border dark:border-gray-700">
                <div className="text-gray-500 dark:text-gray-400">Наличные</div>
                <div className="text-xl font-bold">{totals.cash.toFixed(2)}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:border dark:border-gray-700">
                <div className="text-gray-500 dark:text-gray-400">Карта</div>
                <div className="text-xl font-bold">{totals.card.toFixed(2)}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:border dark:border-gray-700">
                <div className="text-gray-500 dark:text-gray-400">Расходы</div>
                <div className="text-xl font-bold">{totals.credit.toFixed(2)}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:border dark:border-gray-700">
                <div className="text-gray-500 dark:text-gray-400">Инкассация</div>
                <div className="text-xl font-bold">{totals.collection.toFixed(2)}</div>
            </div>
        </div>

        {loading ? <div className="text-gray-500 dark:text-gray-400">Загрузка...</div> : renderTable()}
        </div>
    );
}    