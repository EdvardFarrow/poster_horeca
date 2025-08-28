import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function Analytics() {
  const [rawData, setRawData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [waiters, setWaiters] = useState([]);
  const [selectedWaiters, setSelectedWaiters] = useState([]);

  const [select, setSelect] = useState(["revenue", "profit"]);
  const [interpolate, setInterpolate] = useState("day");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Получаем список официантов
  useEffect(() => {
    const fetchWaiters = async () => {
      try {
        const res = await fetch("/api/users/");
        const json = await res.json();
        setWaiters(json);
      } catch (err) {
        console.error(err);
      }
    };
    fetchWaiters();
  }, []);

  // Автоматический fetch при изменении фильтров
  useEffect(() => {
    if (selectedWaiters.length === 0) return;

    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const url = new URL("/api/analytics/", window.location.origin);
        url.searchParams.set("type", "waiters");
        url.searchParams.set("select", select.join(","));
        url.searchParams.set("interpolate", interpolate);
        url.searchParams.set("id", selectedWaiters.join(","));
        if (dateFrom) url.searchParams.set("dateFrom", dateFrom);
        if (dateTo) url.searchParams.set("dateTo", dateTo);

        const res = await fetch(url);
        const json = await res.json();
        setRawData(json.data || []);
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };

    fetchAnalytics();
  }, [selectedWaiters, select, interpolate, dateFrom, dateTo]);

  // Преобразуем данные для графика
  useEffect(() => {
    if (!rawData.length) return;

    // Группируем по period
    const periodMap = {};
    rawData.forEach((item) => {
      if (!periodMap[item.period]) periodMap[item.period] = { period: item.period };
      select.forEach((metric) => {
        periodMap[item.period][`${metric}_${item.id}`] = item[metric];
      });
    });

    setChartData(Object.values(periodMap));
  }, [rawData, select]);

  const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#a83279", "#32a852"];

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Аналитика</h2>

      {/* фильтры */}
      <div className="flex flex-wrap gap-4 mb-6 items-end">
        <div>
          <label className="block text-sm font-medium">Официанты</label>
          <select
            multiple
            value={selectedWaiters}
            onChange={(e) =>
              setSelectedWaiters(
                Array.from(e.target.selectedOptions, (opt) => opt.value)
              )
            }
            className="border rounded p-2 w-48"
          >
            {waiters.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium">Метрики</label>
          <select
            multiple
            value={select}
            onChange={(e) =>
              setSelect(Array.from(e.target.selectedOptions, (opt) => opt.value))
            }
            className="border rounded p-2 w-48"
          >
            <option value="revenue">Выручка</option>
            <option value="profit">Прибыль</option>
            <option value="transactions">Транзакции</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium">Интервал</label>
          <select
            value={interpolate}
            onChange={(e) => setInterpolate(e.target.value)}
            className="border rounded p-2"
          >
            <option value="day">День</option>
            <option value="week">Неделя</option>
            <option value="month">Месяц</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium">С даты</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="border rounded p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium">По дату</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="border rounded p-2"
          />
        </div>
      </div>

      {/* график */}
      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            {selectedWaiters.map((waiterId, i) =>
              select.map((metric, j) => (
                <Line
                  key={`${waiterId}-${metric}`}
                  type="monotone"
                  dataKey={`${metric}_${waiterId}`}
                  stroke={colors[(i * select.length + j) % colors.length]}
                  name={`${waiters.find((w) => w.id === waiterId)?.name} - ${metric}`}
                />
              ))
            )}
            <CartesianGrid stroke="#ccc" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
