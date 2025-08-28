export default function Sidebar({ activeTab, onChange }) {
    const menu = [
        { id: "reports", label: "Отчеты" },
        { id: "analytics", label: "Аналитика" },
        { id: "salaries", label: "Зарплаты" },
    ];

    return (
        <aside className="w-64 bg-gray-100 border-r p-4">
        <h2 className="text-xl font-bold mb-6">Dashboard</h2>
        <ul className="space-y-2">
            {menu.map((item) => (
            <li key={item.id}>
                <button
                onClick={() => onChange(item.id)}
                className={`w-full text-left px-4 py-2 rounded-xl ${
                    activeTab === item.id
                    ? "bg-blue-600 text-white"
                    : "hover:bg-gray-200"
                }`}
                >
                {item.label}
                </button>
            </li>
            ))}
        </ul>
        </aside>
    );
}
