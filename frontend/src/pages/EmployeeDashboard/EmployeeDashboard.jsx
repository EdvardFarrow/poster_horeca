export default function EmployeeDashboard({ user, shifts = [], salary = [], replacements = [] }) {
  // На случай, если пропсы не пришли
    const userShifts = shifts.length ? shifts : [];
    const userSalary = salary.length ? salary : [];
    const userReplacements = replacements.length ? replacements : [];

    const totalSalary = userSalary.reduce((sum, s) => sum + (s.total || 0), 0);

    return (
        <div className="min-h-screen text-black bg-gray-50 p-6">
        <h1 className="text-3xl font-bold mb-4">Добро пожаловать, {user.fullname || user.username}</h1>

        {/* Личные данные */}
        <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-2">Личные данные</h2>
            <p>Имя: {user.fullname || "-"}</p>
            <p>Роль: {user.role || "-"}</p>
        </section>

        {/* Таблица смен */}
        <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-2">Ваши смены</h2>
            <table className="w-full border border-gray-300">
            <thead className="bg-gray-200">
                <tr>
                <th className="border px-2 py-1">Дата</th>
                <th className="border px-2 py-1">День недели</th>
                <th className="border px-2 py-1">Роль</th>
                <th className="border px-2 py-1">Начало</th>
                <th className="border px-2 py-1">Конец</th>
                </tr>
            </thead>
            <tbody>
                {userShifts.length ? (
                userShifts.map((s, i) => (
                    <tr key={i}>
                    <td className="border px-2 py-1">{s.date}</td>
                    <td className="border px-2 py-1">{s.day}</td>
                    <td className="border px-2 py-1">{s.role}</td>
                    <td className="border px-2 py-1">{s.start}</td>
                    <td className="border px-2 py-1">{s.end}</td>
                    </tr>
                ))
                ) : (
                <tr>
                    <td className="border px-2 py-1 text-center" colSpan={5}>Нет данных</td>
                </tr>
                )}
            </tbody>
            </table>
        </section>

        {/* Зарплата */}
        <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-2">Зарплата за текущий месяц</h2>
            <table className="w-full border border-gray-300">
            <thead className="bg-gray-200">
                <tr>
                <th className="border px-2 py-1">Дата</th>
                <th className="border px-2 py-1">Ставка</th>
                <th className="border px-2 py-1">Процент от выручки</th>
                <th className="border px-2 py-1">Итого</th>
                </tr>
            </thead>
            <tbody>
                {userSalary.length ? (
                userSalary.map((s, i) => (
                    <tr key={i}>
                    <td className="border px-2 py-1">{s.date}</td>
                    <td className="border px-2 py-1">{s.rate}</td>
                    <td className="border px-2 py-1">{s.percent}</td>
                    <td className="border px-2 py-1">{s.total}</td>
                    </tr>
                ))
                ) : (
                <tr>
                    <td className="border px-2 py-1 text-center" colSpan={4}>Нет данных</td>
                </tr>
                )}
            </tbody>
            </table>
            <p className="mt-2 font-semibold">Общий заработок за месяц: {totalSalary}</p>
        </section>

        {/* Запросы на замену */}
        <section>
            <h2 className="text-2xl font-semibold mb-2">Запросы на замену</h2>
            {userReplacements.length ? (
            <table className="w-full border border-gray-300 ">
                <thead className="bg-gray-200">
                <tr>
                    <th className="border px-2 py-1">Дата</th>
                    <th className="border px-2 py-1">Причина</th>
                    <th className="border px-2 py-1">Статус</th>
                </tr>
                </thead>
                <tbody>
                {userReplacements.map((r, i) => (
                    <tr key={i}>
                    <td className="border px-2 py-1">{r.date}</td>
                    <td className="border px-2 py-1">{r.reason}</td>
                    <td className="border px-2 py-1">{r.status}</td>
                    </tr>
                ))}
                </tbody>
            </table>
            ) : (
            <p>Нет активных запросов</p>
            )}
        </section>
        </div>
    );
}
