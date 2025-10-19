import { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { getShiftSales } from "../../api/poster";

const workshopMap = {
    0: "Без цеха",
    1: "Бар",
    2: "Кухня",
    3: "Кальян",
    };

    const getYesterday = () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday;
    };

    const ShiftSales = ({ spotId }) => {
    const [date, setDate] = useState(getYesterday());
    const [salesData, setSalesData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [totalDifference, setTotalDifference] = useState(0);
    const [tipsByService, setTipsByService] = useState({});

    const [search, setSearch] = useState("");
    const [workshopFilter, setWorkshopFilter] = useState("all");
    const [categoryFilter, setCategoryFilter] = useState("all");
    const [sortConfig, setSortConfig] = useState({ key: null, direction: null });
    const token = localStorage.getItem("access");

    const formatLocalDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    };

    const formatNumber = (num) => {
        const n = Number(num);
        return Number.isInteger(n) ? n : n.toFixed(2);
    };
    
    const fetchShiftSales = async (selectedDate) => {
        setLoading(true);
        try {
        const formattedDate = formatLocalDate(selectedDate);
        const data = await getShiftSales(formattedDate, spotId);
        const allShifts = Object.values(data || []);

        const allProducts = allShifts.flatMap((s) => [
            ...(s.regular || []).map((p) => ({ ...p, category: "regular", shiftId: s.shift_id })),
            ...(s.delivery || []).map((p) => ({
            ...p,
            category: "delivery",
            shiftId: s.shift_id,
            delivery_service: p.delivery_service || "Другое",
            })),
        ]);
        setSalesData(allProducts);

        const tipsMap = {};
        allShifts.forEach((s) => {
            if (s.tips_by_service) {
            Object.entries(s.tips_by_service).forEach(([service, value]) => {
                tipsMap[service] = (tipsMap[service] || 0) + parseFloat(value || 0);
            });
            }
        });
        setTipsByService(tipsMap);

        const totalDiff = allShifts.reduce((sum, s) => sum + (s.difference || 0), 0);
        setTotalDifference(totalDiff);
        } catch (err) {
        console.error("Ошибка загрузки смен:", err);
        setSalesData([]);
        setTotalDifference(0);
        setTipsByService({});
        } finally {
        setLoading(false);
        }
    };
    
    useEffect(() => {
        fetchShiftSales(date);
    }, [date, spotId]);

    const totalProfit = salesData.reduce((sum, p) => sum + (parseFloat(p.profit) || 0), 0);
    const totalPayedSum = salesData.reduce((sum, p) => sum + (parseFloat(p.payed_sum) || 0), 0);

    const filteredData = salesData.filter((p) => {
        const matchesWorkshop = workshopFilter === "all" || String(p.workshop) === workshopFilter;
        const matchesSearch = p.product_name.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = categoryFilter === "all" || p.category === categoryFilter;
        return matchesWorkshop && matchesSearch && matchesCategory;
    });

    const sortedData = [...filteredData].sort((a, b) => {
        if (!sortConfig.key) return 0;
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        const numericKeys = ["count", "price", "payed_sum", "profit", "workshop"];
        if (numericKeys.includes(sortConfig.key)) {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
        }

        if (typeof aVal === "string") {
        return sortConfig.direction === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        } else {
        return sortConfig.direction === "asc" ? aVal - bVal : bVal - aVal;
        }
    });

    const requestSort = (key) => {
        if (sortConfig.key === key) {
        if (sortConfig.direction === "asc") setSortConfig({ key, direction: "desc" });
        else if (sortConfig.direction === "desc") setSortConfig({ key: null, direction: null });
        } else {
        setSortConfig({ key, direction: "asc" });
        }
    };

    const renderSortArrow = (key) => {
        if (sortConfig.key !== key) return null;
        return sortConfig.direction === "asc" ? " ▲" : " ▼";
    };

    const highlight = (text) => {
        if (!search) return text;
        const regex = new RegExp(`(${search})`, "gi");
        return text.split(regex).map((part, i) =>
        regex.test(part) ? <span key={i} className="bg-yellow-200 font-bold">{part}</span> : part
        );
    };

    const calculateWorkshopStats = (category) => {
        return Object.entries(workshopMap)
        .filter(([id]) => Number(id) !== 0 && (category === "delivery" ? Number(id) !== 3 : true))
        .map(([id, name]) => {
            const filtered = salesData.filter((p) => p.category === category && Number(p.workshop) === Number(id));
            const sumPayed = filtered.reduce((s, p) => s + (parseFloat(p.payed_sum) || 0), 0);
            const sumProfit = filtered.reduce((s, p) => s + (parseFloat(p.profit) || 0), 0);
            return { id, name, sumPayed, sumProfit };
        });
    };

    const regularWorkshops = calculateWorkshopStats("regular");
    const deliveryWorkshops = calculateWorkshopStats("delivery");


    const saveShiftSales = async () => {
        try {
            const dateStr = formatLocalDate(date);

            let shiftId;
            const shiftCheckResponse = await fetch(`/api/shift_sales/?date=${dateStr}`, {
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                }
            });
            
            const shifts = await shiftCheckResponse.json();
            console.log('ШИФТ', shifts)

            if (shifts.length > 0) {
            shiftId = shifts[0].shift_id; 
            }
            else    {
                alert("Shift bot found")
            }
            
            



            console.log("shiftId:", shiftId);
            if (!shiftId) {
            alert("Не удалось получить или создать смену!");
            return;
            }



            const payload = {
            items: salesData.map((p) => ({
                shift_sale: shiftId,
                product_name: p.product_name,
                count: Number(p.count) || 0,
                product_sum: Number(p.product_sum) || 0,
                payed_sum: Number(p.payed_sum) || 0,
                profit: Number(p.profit) || 0,
                workshop: p.workshop,
                category_name: p.category,
                delivery_service: p.delivery_service || null,
                tips: 0,
            })),
            };

            console.log("Payload для сохранения:", payload);

            const response = await fetch("/api/shift_sales_item/", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error("Ошибка сохранения");

            const result = await response.json();
            console.log("Сохранено:", result);
            alert("Данные успешно сохранены!");
        } catch (err) {
            console.error("Ошибка сохранения:", err);
            alert("Не удалось сохранить данные");
        }
    };

    return (
        <div className="p-4 text-gray-900 dark:text-gray-100">
        <h2 className="text-xl font-bold mb-4">Продажи смены</h2>

        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-2 items-center">
            <DatePicker 
                selected={date} 
                onChange={(d) => setDate(d)} 
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100" 
            />
            <button 
                onClick={() => fetchShiftSales(date)} 
                className="px-3 py-1 border rounded bg-white text-gray-800 hover:bg-gray-100 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
            >
                Обновить
            </button>
            <input
                type="text"
                placeholder="Поиск по товару..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
            />
            <select
                value={workshopFilter}
                onChange={(e) => setWorkshopFilter(e.target.value)}
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
            >
                <option value="all">Все цеха</option>
                {Object.entries(workshopMap).map(([id, name]) => (
                    <option key={id} value={id}>
                        {id} – {name}
                    </option>
                ))}
            </select>
            <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="border px-2 py-1 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
            >
                <option value="all">Все категории</option>
                <option value="regular">Зал</option>
                <option value="delivery">Доставка</option>
            </select>
        </div>

        {/* General Stats */}
        <div className="mb-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div className="p-4 border rounded-lg shadow-sm flex flex-col justify-between col-span-1 sm:col-span-2 md:col-span-3 lg:col-span-4 bg-white dark:bg-gray-800 dark:border-gray-700">
                <h3 className="font-semibold mb-2">Общие показатели</h3>
                <div>Общая прибыль: <strong>{formatNumber(totalProfit)}</strong></div>
                <div>Выручка: <strong>{formatNumber(totalPayedSum)}</strong></div>
                {Object.keys(tipsByService).length > 0 && (
                    <div>Процент: <strong>{formatNumber(Object.values(tipsByService).reduce((sum, val) => sum + val, 0))}</strong></div>
                )}
                <div>Общая выручка: <strong>{formatNumber(Number(totalPayedSum) + Object.values(tipsByService).reduce((sum, val) => sum + val, 0))}</strong></div>
            </div>
        </div>

        {/* In-house Block */}
        <div className="mb-6">
            <h3 className="font-bold mb-2">Зал</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 items-stretch">
                {regularWorkshops.map(({ id, name, sumPayed, sumProfit }) => (
                    <div key={id} className="p-4 border rounded-lg shadow-sm flex flex-col justify-between bg-white dark:bg-gray-800 dark:border-gray-700">
                        <span className="font-medium">{name}</span>
                        <span>Выручка: <strong>{formatNumber(sumPayed)}</strong></span>
                        <span>Прибыль: <strong>{formatNumber(sumProfit)}</strong></span>
                    </div>
                ))}
                <div className="p-4 border rounded-lg shadow-sm flex flex-col justify-between bg-gray-100 dark:bg-gray-700 dark:border-gray-600">
                    <span className="font-bold">Общий зал</span>
                    <span>Выручка: <strong>{formatNumber(regularWorkshops.reduce((acc, w) => acc + w.sumPayed, 0))}</strong></span>
                    <span>Прибыль: <strong>{formatNumber(regularWorkshops.reduce((acc, w) => acc + w.sumProfit, 0))}</strong></span>
                </div>
            </div>
        </div>

        {/* Delivery Block */}
        <div className="mb-6">
            <h3 className="font-bold mb-2">Доставка</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 items-stretch">
                {Object.entries(
                    salesData
                        .filter((p) => p.category === "delivery")
                        .reduce((acc, p) => {
                            const service = p.delivery_service || "Другое";
                            if (!acc[service]) {
                                acc[service] = { sumPayed: 0, sumProfit: 0 };
                            }
                            acc[service].sumPayed += parseFloat(p.payed_sum) || 0;
                            acc[service].sumProfit += parseFloat(p.profit) || 0;
                            return acc;
                        }, {})
                ).map(([service, stats]) => (
                    <div key={service} className="p-4 border rounded-lg shadow-sm flex flex-col justify-between bg-white dark:bg-gray-800 dark:border-gray-700">
                        <span className="font-medium">{service}</span>
                        <span>Выручка: <strong>{formatNumber(stats.sumPayed)}</strong></span>
                        <span>Прибыль: <strong>{formatNumber(stats.sumProfit)}</strong></span>
                        <span>Процент: <strong>{formatNumber(tipsByService[service] || 0)}</strong></span>
                        <span>Общая Выручка: <strong>{formatNumber((Number(tipsByService[service] || 0) || 0) + (Number(stats.sumPayed) || 0))}</strong></span>
                    </div>
                ))}
                <div className="p-4 border rounded-lg shadow-sm flex flex-col justify-between bg-gray-100 dark:bg-gray-700 dark:border-gray-600">
                    <span className="font-bold">Общая доставка</span>
                    <span>Выручка: <strong>{formatNumber(salesData.filter(p => p.category === "delivery").reduce((acc, p) => acc + (parseFloat(p.payed_sum) || 0), 0))}</strong></span>
                    <span>Прибыль: <strong>{formatNumber(salesData.filter(p => p.category === "delivery").reduce((acc, p) => acc + (parseFloat(p.profit) || 0), 0))}</strong></span>
                    <span>Процент: <strong>{formatNumber(Object.values(tipsByService).reduce((a, b) => a + b, 0))}</strong></span>
                </div>
            </div>
        </div>

        {/* Products Table */}
        {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Загрузка...</p>
        ) : sortedData.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">Нет данных за выбранную дату</p>
        ) : (
            <div className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-100 dark:bg-gray-700">
                        <tr className="border-b dark:border-gray-700">
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("product_name")}>
                                Товар{renderSortArrow("product_name")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("count")}>
                                Кол-во{renderSortArrow("count")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("product_sum")}>
                                Цена{renderSortArrow("product_sum")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("payed_sum")}>
                                Оплачено{renderSortArrow("payed_sum")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("profit")}>
                                Прибыль{renderSortArrow("profit")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("workshop")}>
                                Цех{renderSortArrow("workshop")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 cursor-pointer font-semibold" onClick={() => requestSort("category")}>
                                Категория{renderSortArrow("category")}
                            </th>
                            <th className="px-4 py-2 border dark:border-gray-600 font-semibold">Сервис доставки</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedData.map((p, idx) => (
                            <tr key={idx} className="border-t dark:border-gray-700 odd:bg-white even:bg-gray-50 dark:odd:bg-gray-800 dark:even:bg-gray-700">
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{highlight(p.product_name)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{formatNumber(p.count)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{formatNumber(p.product_sum)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{formatNumber(p.payed_sum)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{formatNumber(p.profit)}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{workshopMap[p.workshop] || p.workshop}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{p.category === "delivery" ? "Доставка" : "Зал"}</td>
                                <td className="px-4 py-2 border dark:border-gray-600 text-center">{p.category === "delivery" ? p.delivery_service || "Другое" : ""}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        )}
    </div>
);
};

export default ShiftSales;