import axios from "axios";

/**
 * Получение аналитики с бэка
 * @param {Object} options
 * @param {string} options.type - Тип аналитики: waiters, clients, products, finance и т.д.
 * @param {Array<string>} options.select - Список метрик: revenue, profit, orders, count и т.д.
 * @param {string|null} options.dateFrom - Дата начала (YYYY-MM-DD), если null — берёт последние 30 дней
 * @param {string|null} options.dateTo - Дата конца (YYYY-MM-DD), если null — сегодня
 * @param {string} options.interpolate - "day", "week" или "month"
 * @param {boolean} options.business_day - true/false
 */
export async function getStatistics({
  type = "finance",
  select = ["revenue", "profit"],
  dateFrom = null,
  dateTo = null,
  interpolate = "day",
  business_day = true,
}) {
  try {
    const token = localStorage.getItem("access");
    if (!token) throw new Error("Токен отсутствует, пользователь не залогинен");

    // Если даты не указаны, ставим последние 30 дней
    const today = new Date();
    const to = dateTo || today.toISOString().split("T")[0];
    const from = dateFrom || new Date(today.setDate(today.getDate() - 30)).toISOString().split("T")[0];

    const params = {
      type,
      select: select.join(","),
      dateFrom: from,
      dateTo: to,
      interpolate,
      business_day,
    };

    const { data } = await axios.get("http://127.0.0.1:8000/api/statistics/", {
      headers: { Authorization: `Bearer ${token}` },
      params,
    });

    // Бэкенд возвращает { type: "...", data: [...] }
    return data.data || data; // если нет поля data, возвращаем raw
  } catch (err) {
    console.error("Ошибка получения аналитики:", err);
    return [];
  }
}



export async function getCashShifts({ dateFrom = null, dateTo = null, spot_id = null } = {}) {
  try {
    const token = localStorage.getItem("access");
    if (!token) throw new Error("Токен отсутствует, пользователь не залогинен");

    const today = new Date();

    const formatDate = (d) => {
      const date = new Date(d);
      const yyyy = date.getFullYear();
      const mm = String(date.getMonth() + 1).padStart(2, "0");
      const dd = String(date.getDate()).padStart(2, "0");
      return `${yyyy}${mm}${dd}`;
    };

    const from = dateFrom ? formatDate(dateFrom) : formatDate(new Date(today.setDate(today.getDate() - 30)));
    const to = dateTo ? formatDate(dateTo) : formatDate(new Date());

    const params = { dateFrom: from, dateTo: to };
    if (spot_id) params.spot_id = spot_id;

    const { data } = await axios.get("http://127.0.0.1:8000/api/cash_shifts/", {
      headers: { Authorization: `Bearer ${token}` },
      params,
    });


    if (!data || !Array.isArray(data)) return [];

    return data.map(shift => ({
      timestart: shift.date_start,
      timeend: shift.date_end,
      amount_start: shift.amount_start,
      amount_end: shift.amount_end,
      amount_sell_cash: shift.amount_sell_cash,
      amount_sell_card: shift.amount_sell_card,
      amount_credit: shift.amount_credit,
      amount_collection: shift.amount_collection,
      user_id_start: shift.user_id_start,
      user_id_end: shift.user_id_end,
      comment: shift.comment,
    }));
  } catch (err) {
    console.error("Ошибка получения кассовых смен:", err);
    return [];
  }
}


export async function getEmployees() {
  try {
    const token = localStorage.getItem("access");
    if (!token) throw new Error("Токен отсутствует, пользователь не залогинен");

    const { data } = await axios.get("http://127.0.0.1:8000/api/employees/", {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!data || !Array.isArray(data)) return [];

    // Приводим к удобному виду для таблицы
    return data.map(emp => ({
      poster_id: emp.poster_id,
      name: emp.name,
      role_name: emp.role_name || "",
      phone: emp.phone || "",
      last_in: emp.last_in || "",
    }));
  } catch (err) {
    console.error("Ошибка получения сотрудников:", err);
    return [];
  }
}


export async function getShiftSales(date, spotId) {
  const params = new URLSearchParams();
  if (date) params.append("date", date);
  if (spotId) params.append("spot_id", spotId);

  const url = `/api/shift_sales/?${params.toString()}`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access")}`,
    },
  });

  const text = await response.text();

  if (!response.ok) throw new Error("Ошибка загрузки данных смен");

  try {
    return JSON.parse(text);
  } catch (err) {
    console.error("[API] Не удалось распарсить JSON:", err);
    throw new Error("Ответ с сервера не является JSON");
  }
}
