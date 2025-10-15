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
        <table className="min-w-full border border-gray-300">
            <thead className="bg-gray-200">
            <tr>
                {headers.map((h) => (
                <th key={h} className="px-4 py-2 border">
                    {headerLabels[h]}
                </th>
                ))}
            </tr>
            </thead>
            <tbody>
            {data.map((row, idx) => (
                <tr key={idx} className="odd:bg-white even:bg-gray-100">
                <td className="px-4 py-2 border">{formatDate(row.timestart)}</td>
                <td className="px-4 py-2 border">{formatDate(row.timeend)}</td>
                <td className="px-4 py-2 border">{(row.amount_start || 0).toFixed(2)}</td>
                <td className="px-4 py-2 border">{(row.amount_end || 0).toFixed(2)}</td>
                <td className="px-4 py-2 border">{(row.amount_sell_cash || 0).toFixed(2)}</td>
                <td className="px-4 py-2 border">{(row.amount_sell_card || 0).toFixed(2)}</td>
                <td className="px-4 py-2 border">{((row.amount_sell_cash || 0) + (row.amount_sell_card || 0)).toFixed(2)}</td>
                <td className="px-4 py-2 border">{(row.amount_credit || 0).toFixed(2)}</td>
                <td className="px-4 py-2 border">{(row.amount_collection || 0).toFixed(2)}</td>
                </tr>
            ))}
            </tbody>
        </table>
        );
    };

    return (
        <div>
        {/* Фильтр по датам */}
        <div className="mb-4 flex gap-2 items-center flex-wrap">
            <span>С:</span>
            <DatePicker
            selected={dateFrom}
            onChange={setDateFrom}
            dateFormat="yyyy-MM-dd"
            />
            <span>По:</span>
            <DatePicker
            selected={dateTo}
            onChange={setDateTo}
            dateFormat="yyyy-MM-dd"
            />
            <button
            onClick={() => {
                setDateFrom(null);
                setDateTo(null);
            }}
            className="bg-gray-300 text-white px-2 py-1 rounded"
            >
            Сбросить
            </button>
            <select value={spotId} onChange={e => setSpotId(Number(e.target.value))}>
                <option value={1}>Ресторан</option>
                <option value={2}>Доставка</option>
            </select>
        </div>

        {/* Итоги */}
        <div className="mb-4 flex gap-4 flex-wrap">
            <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500">Общая выручка</div>
            <div className="text-xl font-bold">{totals.revenue.toFixed(2)}</div>
            </div>
            <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500">Наличные</div>
            <div className="text-xl font-bold">{totals.cash.toFixed(2)}</div>
            </div>
            <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500">Карта</div>
            <div className="text-xl font-bold">{totals.card.toFixed(2)}</div>
            </div>
            <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500">Расходы</div>
            <div className="text-xl font-bold">{totals.credit.toFixed(2)}</div>
            </div>
            <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500">Инкассация</div>
            <div className="text-xl font-bold">{totals.collection.toFixed(2)}</div>
            </div>
        </div>

        {loading ? <div>Загрузка...</div> : renderTable()}
        </div>
    );
    }
