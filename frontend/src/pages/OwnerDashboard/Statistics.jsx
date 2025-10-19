import { useState, useEffect } from "react";
import { getStatistics } from "../../api/poster"; 
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

export default function Statistics() {
  const TYPES = ["waiters", "clients", "products", "categories"];

  const METRIC_LABELS = {
    revenue: "Выручка",
    profit: "Прибыль",
    orders: "Чеки",
    avg_check: "Средний чек",
    clients: "Клиенты",
    phone: "Телефон",
    data: "Сумма продаж",
    data_hourly: "Почасовые продажи",
    data_weekday: "Продажи по дням недели",
    counters: "Счётчики",
    transaction_id: "Номер заказа",
    sum: "Сумма",
    count: "Количество",
    orders_count: "Кол-во заказов",
    average_receipt: "Средний чек",
    average_time: "Среднее время",
    product_name: "Продукт",
    employee_name: "Сотрудник",
    name: "Клиент",
    visits: "Посещения",
    product_profit: "Прибыль",
    category_name: "Категория",
    };

  const METRICS = {
    waiters: [],
    clients: [],
    products: [],
    categories: [],
  };

  const [type, setType] = useState("waiters");
  const [metrics, setMetrics] = useState(METRICS["waiters"]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);

  const PAGE_SIZE = 30;

  useEffect(() => {
    fetchData(1, type, metrics, dateFrom, dateTo);
  }, [type, metrics, dateFrom, dateTo]);

  async function fetchData(pageNumber, type, selectedMetrics, from, to) {
    setLoading(true);
    try {
      const rawData = await getStatistics({
        type,
        select: selectedMetrics,
        dateFrom: from,
        dateTo: to,
        interpolate: "day",
        business_day: true
      });

      // Если ответ с объектом counters или data, приводим к массиву для отображения
      let formattedData = [];
      if (Array.isArray(rawData)) {
        formattedData = rawData;
      } else if (rawData.counters) {
        formattedData = [rawData.counters];
      } else {
        formattedData = [rawData];
      }

      setData(formattedData.slice(0, PAGE_SIZE * pageNumber));
      setPage(pageNumber);
    } catch (err) {
      console.error("Ошибка получения аналитики:", err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }

  const handleLoadMore = () => {
    fetchData(page + 1, type, metrics, dateFrom, dateTo);
  };

  const handleTypeChange = (newType) => {
    setType(newType);
    setMetrics(METRICS[newType]);
    setData([]);
    setPage(1);
  };

  const handleMetricToggle = (metric) => {
    setMetrics(prev =>
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const renderTable = () => {
    if (!data || data.length === 0) return <div>Нет данных</div>;

    const headers = Object.keys(data[0] || {});
    return (
      <table className="min-w-full border border-gray-300">
        <thead className="bg-gray-200">
          <tr>
            {headers.map(h => (
              <th key={h} className="px-4 py-2 border">
                {METRIC_LABELS[h] || h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className="odd:bg-white even:bg-gray-100">
              {headers.map(h => <td key={h} className="px-4 py-2 border">{row[h]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-4">Статистика</h1>

      {/* Выбор типа */}
      <div className="mb-4 flex gap-2">
        {TYPES.map(t => (
          <button
            key={t}
            onClick={() => handleTypeChange(t)}
            className={`px-3 py-1 rounded ${t === type ? "bg-indigo-600 text-white" : "bg-gray-300"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Метрики */}
      <div className="mb-4 flex gap-2 flex-wrap">
        {METRICS[type].map(metric => (
          <label key={metric} className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={metrics.includes(metric)}
              onChange={() => handleMetricToggle(metric)}
            />
            {METRIC_LABELS[metric] || metric}
          </label>
        ))}
      </div>

      {/* Фильтры по датам */}
      <div className="mb-4 flex gap-2 items-center flex-wrap">
        <span>С:</span>
        <DatePicker selected={dateFrom} onChange={setDateFrom} dateFormat="yyyy-MM-dd" />
        <span>По:</span>
        <DatePicker selected={dateTo} onChange={setDateTo} dateFormat="yyyy-MM-dd" />
        <button
          onClick={() => { setDateFrom(null); setDateTo(null); }}
          className="bg-gray-300 px-2 py-1 rounded"
        >
          Сбросить
        </button>
      </div>

      {loading ? <div>Загрузка...</div> : renderTable()}

      {data.length >= PAGE_SIZE * page && (
        <div className="mt-4">
          <button onClick={handleLoadMore} className="bg-indigo-600 text-white px-4 py-2 rounded">
            Загрузить ещё
          </button>
        </div>
      )}
    </div>
  );
}
