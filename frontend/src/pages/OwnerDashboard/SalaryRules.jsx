import { useState, useEffect } from "react";
import axios from "axios";

export default function SalaryRules() {
    const [salaryRules, setSalaryRules] = useState([]);
    const [roles, setRoles] = useState([]);
    const [workshops, setWorkshops] = useState([]);
    const [productsList, setProductsList] = useState([]);

    const [selectedRole, setSelectedRole] = useState("");
    const [fixedPerShift, setFixedPerShift] = useState("");
    const [selectedWorkshops, setSelectedWorkshops] = useState([]);
    const [selectedProducts, setSelectedProducts] = useState([]);
    const [fixedPerProduct, setFixedPerProduct] = useState({});
    const [percent, setPercent] = useState("");
    const token = localStorage.getItem("access");

    const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

    useEffect(() => {
        if (!token) return;

        axios.get("/api/auth/role/", axiosConfig).then(res => setRoles(res.data)).catch(console.error);
        axios.get("/api/poster_api_workshop/", axiosConfig).then(res => setWorkshops(res.data)).catch(console.error);
        axios.get("/api/poster_api_product/", axiosConfig).then(res => setProductsList(res.data)).catch(console.error);
        axios.get("/api/salary_rules/", axiosConfig).then(res => setSalaryRules(res.data)).catch(console.error);
    }, [token]);

    const filteredProducts = productsList.filter(p =>
        selectedWorkshops.map(Number).includes(Number(p.workshop_id))
    );

    const addProduct = () => setSelectedProducts([...selectedProducts, null]);

    const updateProduct = (index, productId) => {
        const newProducts = [...selectedProducts];
        newProducts[index] = productId ? Number(productId) : null;
        setSelectedProducts(newProducts);
    };

    const updateFixed = (productId, value) => {
        if (!productId) return;
        setFixedPerProduct({ ...fixedPerProduct, [productId]: Number(value) });
    };

    const removeProduct = (index) => {
        const newProducts = [...selectedProducts];
        const removed = newProducts.splice(index, 1)[0];
        setSelectedProducts(newProducts);
        const newFixed = { ...fixedPerProduct };
        if (removed) delete newFixed[removed];
        setFixedPerProduct(newFixed);
    };

    const addSalaryRule = () => {
        if (!selectedRole) return;

        const cleanWorkshops = selectedWorkshops.filter(w => w !== null && w !== "");
        const cleanProducts = selectedProducts.filter(p => p !== null && p !== "");

        // Формируем product_fixed с правильными ID и fixed
        const product_fixed = cleanProducts.map(p => ({
            product: p,
            fixed: fixedPerProduct[p] || 0
        }));

        const payload = {
            role: Number(selectedRole),
            percent: percent ? Number(percent) : null,
            fixed_per_shift: fixedPerShift ? Number(fixedPerShift) : null,
            workshops: cleanWorkshops.map(Number),
            product_fixed: cleanProducts
                .filter(p => p)
                .map(p => {
                    const productObj = filteredProducts.find(prod => Number(prod.id) === Number(p));
                    return {
                        product: productObj ? productObj.id : null, 
                        fixed: Number(fixedPerProduct[p] || 0)
                    };
            })
        };

        console.log("Payload перед отправкой:", payload);
        axios.post("/api/salary_rules/", payload, axiosConfig)
            .then(res => {
                setSalaryRules([...salaryRules, res.data]);
                setSelectedRole("");
                setSelectedWorkshops([]);
                setSelectedProducts([]);
                setFixedPerProduct({});
                setPercent("");
                setFixedPerShift("");
            })
            .catch(err => {
                if (err.response) {
                    console.error("Ошибка API:", err.response.data);
                    console.error("Статус:", err.response.status);
                } else if (err.request) {
                    console.error("Запрос ушёл, но ответа нет:", err.request);
                } else {
                    console.error("Axios ошибка:", err.message);
                }
            });
    };

    return (
        <div>
            <h2 className="text-2xl font-semibold mb-4">Формулы зарплаты</h2>

            <div className="flex flex-col gap-2 mb-4">
                <select
                    value={selectedRole}
                    onChange={e => setSelectedRole(e.target.value)}
                    className="border p-2 rounded"
                >
                    <option value="">Выберите роль</option>
                    {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>

                <input
                    type="number"
                    placeholder="% от выручки"
                    value={percent}
                    onChange={e => setPercent(e.target.value)}
                    className="border p-2 rounded"
                />

                <input
                    type="number"
                    placeholder="Фикс за смену"
                    value={fixedPerShift}
                    onChange={e => setFixedPerShift(e.target.value)}
                    className="border p-2 rounded"
                />

                {/* Цеха */}
                <div>
                    <label className="block mb-1">Цеха</label>
                    {selectedWorkshops.map((w, idx) => (
                        <div key={idx} className="flex gap-2 mb-2">
                            <select
                                value={w ?? ""}
                                onChange={e => {
                                    const newSelected = [...selectedWorkshops];
                                    newSelected[idx] = e.target.value ? Number(e.target.value) : null;
                                    setSelectedWorkshops(newSelected);
                                }}
                                className="border p-2 rounded flex-1"
                            >
                                <option value="">Выберите цех</option>
                                {workshops.map(ws => <option key={ws.id} value={ws.id}>{ws.name}</option>)}
                            </select>
                            <button onClick={() => {
                                const newSelected = [...selectedWorkshops];
                                newSelected.splice(idx, 1);
                                setSelectedWorkshops(newSelected);
                            }} className="bg-red-500 text-white px-2 rounded">Удалить</button>
                        </div>
                    ))}
                    <button onClick={() => setSelectedWorkshops([...selectedWorkshops, null])}
                        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                        Ещё цех
                    </button>
                </div>

                {/* Продукты */}
                <div>
                    <label className="block mb-1">Продукты</label>
                    {selectedProducts.map((p, idx) => (
                        <div key={idx} className="flex gap-2 mb-2">
                            
                            <select
                            
                                value={p ?? ""}
                                onChange={e => updateProduct(idx, e.target.value)}
                                className="border p-2 rounded flex-1"
                            >
                                <option value="">Выберите продукт</option>
                                {console.log("Filtered products для селекта:", filteredProducts)}
                                {filteredProducts.map(prod => <option key={prod.id} value={prod.id}>{prod.name}</option>)}
                            </select>
                            <input
                                type="number"
                                placeholder="Фикс за товар"
                                value={p ? fixedPerProduct[p] || "" : ""}
                                onChange={e => updateFixed(p, e.target.value)}
                                className="border p-2 rounded w-32"
                                disabled={!p}
                            />
                            <button onClick={() => removeProduct(idx)} className="bg-red-500 text-white px-2 rounded">Удалить</button>
                        </div>
                    ))}
                    <button onClick={addProduct} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">Ещё продукт</button>
                </div>

                <button onClick={addSalaryRule} className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 mt-2">
                    Добавить правило
                </button>
            </div>

            {/* Таблица правил */}
            <table className="w-full border border-gray-300 text-center">
                <thead>
                    <tr className="bg-gray-200">
                        <th className="p-2">Роль</th>
                        <th className="p-2">% от выручки</th>
                        <th className="p-2">Фикс за смену</th>
                        <th className="p-2">Цех</th>
                        <th className="p-2">Продукты и фикс</th>
                    </tr>
                </thead>
                <tbody>
                    {salaryRules.map(r => (
                        <tr key={r.id} className="border-t border-gray-300">
                            <td className="p-2">{r.role_name ?? r.role ?? "-"}</td>
                            <td className="p-2">{r.percent ?? "-"}</td>
                            <td className="p-2">{r.fixed_per_shift ?? "-"}</td>
                            <td className="p-2">
                                {Array.isArray(r.workshops) && r.workshops.length > 0
                                ? r.workshops.map(id => {
                                    const ws = workshops.find(w => w.id === id);
                                    return ws?.name ?? id;
                                }).join(", ")
                                : "-"}
                            </td>
                            <td className="p-2">
                                {Array.isArray(r.product_fixed) && r.product_fixed.length > 0
                                    ? r.product_fixed.map(pf => (
                                        <div key={pf.product_name ?? pf.product}>
                                            {(pf.product_name ?? pf.product) + ": " + pf.fixed}
                                        </div>
                                    ))
                                    : "-"}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
