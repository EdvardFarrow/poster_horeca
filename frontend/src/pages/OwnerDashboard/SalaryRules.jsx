import { useState, useEffect } from "react";
import api from "../../api";

export default function SalaryRules() {
    const [salaryRules, setSalaryRules] = useState([]);
    const [roles, setRoles] = useState([]);
    const [workshops, setWorkshops] = useState([]);
    const [productsList, setProductsList] = useState([]);

    const [editingRule, setEditingRule] = useState(null); 
    const [selectedRole, setSelectedRole] = useState("");
    const [fixedPerShift, setFixedPerShift] = useState("");
    const [selectedWorkshops, setSelectedWorkshops] = useState([]);
    const [selectedProducts, setSelectedProducts] = useState([]);
    const [fixedPerProduct, setFixedPerProduct] = useState({});
    const [percent, setPercent] = useState("");

    const [isProductsVisible, setIsProductsVisible] = useState(true); 

    const fetchRules = () => {
        api.get("/api/salary_rules/")
            .then(res => setSalaryRules(res.data))
            .catch(console.error);
    };

    useEffect(() => {
        api.get("/api/auth/role/").then(res => setRoles(res.data)).catch(console.error);
        api.get("/api/poster_api_workshop/").then(res => setWorkshops(res.data)).catch(console.error);
        api.get("/api/poster_api_product/").then(res => setProductsList(res.data)).catch(console.error);
        fetchRules();
    }, []); 

    const filteredProducts = productsList.filter(p =>
        selectedWorkshops.map(Number).includes(Number(p.workshop_id))
    );

    const handlePositiveNumericChange = (value, setter) => {
        let processedValue = value;
        if (parseFloat(value) < 0) {
            processedValue = '0';
        }
        setter(processedValue);
    };

    const addProduct = () => setSelectedProducts([...selectedProducts, null]);

    const updateProduct = (index, productId) => {
        const newProducts = [...selectedProducts];
        newProducts[index] = productId ? Number(productId) : null;
        setSelectedProducts(newProducts);
    };

    const updateFixed = (productId, value) => {
        if (!productId) return;
        let processedValue = value;
        if (parseFloat(value) < 0) {
            processedValue = '0';
        }
        setFixedPerProduct({ ...fixedPerProduct, [productId]: processedValue });
    };

    const removeProduct = (index) => {
        const newProducts = [...selectedProducts];
        const removed = newProducts.splice(index, 1)[0];
        setSelectedProducts(newProducts);
        const newFixed = { ...fixedPerProduct };
        if (removed) delete newFixed[removed];
        setFixedPerProduct(newFixed);
    };

    const resetForm = () => {
        setEditingRule(null);
        setSelectedRole("");
        setSelectedWorkshops([]);
        setSelectedProducts([]);
        setFixedPerProduct({});
        setPercent("");
        setFixedPerShift("");
    };

    const handleEditClick = (rule) => {
        setEditingRule(rule); 
        setSelectedRole(rule.role);
        setPercent(rule.percent || "");
        setFixedPerShift(rule.fixed_per_shift || "");
        setSelectedWorkshops(rule.workshops || []);
        
        const correctProductIds = [];
        const correctProductFixedMap = {};

        rule.product_fixed.forEach(pf_from_api => {
            const externalProductId = pf_from_api.product; 

            const matchingProduct = productsList.find(
                p => Number(p.product_id) === Number(externalProductId)
            );

            if (matchingProduct) {
                const internalDjangoId = matchingProduct.id; 
                correctProductIds.push(internalDjangoId);
                correctProductFixedMap[internalDjangoId] = pf_from_api.fixed;
            } else {
                console.warn(`Продукт с внешним ID ${externalProductId} не найден. Пропускаем.`);
            }
        });

        setSelectedProducts(correctProductIds);
        setFixedPerProduct(correctProductFixedMap);
    };

    const handleDeleteRule = (ruleId) => {
        if (!window.confirm("Вы уверены, что хотите удалить это правило?")) return;

        api.delete(`/api/salary_rules/${ruleId}/`)
            .then(() => {
                setSalaryRules(prevRules => prevRules.filter(r => r.id !== ruleId));
            })
            .catch(err => console.error("Ошибка удаления:", err));
    };

    const handleSubmit = () => {
        if (!selectedRole) return;

        const cleanWorkshops = selectedWorkshops.filter(w => w !== null && w !== "");
        const cleanProducts = selectedProducts.filter(p => p !== null && p !== "");

        const payload = {
            role: Number(selectedRole),
            percent: percent ? Number(percent) : null,
            fixed_per_shift: fixedPerShift ? Number(fixedPerShift) : null,
            workshops: cleanWorkshops.map(Number),
            
            product_fixed: cleanProducts.map(internalProductId => ({
                product: internalProductId, 
                fixed: Number(fixedPerProduct[internalProductId] || 0)
            }))
        };
        console.log("[SUBMIT] Отправляю на сервер:", payload);
        const isEditing = editingRule !== null;

        const request = isEditing
            ? api.patch(`/api/salary_rules/${editingRule.id}/`, payload)
            : api.post("/api/salary_rules/", payload);

        request.then(res => {
            fetchRules();
            resetForm();
        })
        .catch(err => {
            if (err.response) {
                console.error("Ошибка API:", err.response.data);
                console.error("Статус:", err.response.status);
            } else if (err.request) {
                console.error("Запрос ушёл, но ответа нет:", err.request);
            } else {
                console.error("Ошибка:", err.message);
            }
        });
    };


    return (
        <div className="text-gray-900 dark:text-gray-100">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold">
                    {editingRule ? "Редактирование правила" : "Формулы зарплаты"}
                </h2>
                <button 
                    onClick={() => setIsProductsVisible(!isProductsVisible)}
                    className="text-sm bg-gray-200 text-gray-800 px-3 py-1 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                >
                    {isProductsVisible ? "Скрыть продукты" : "Показать продукты"}
                </button>
            </div>

            <div className="flex flex-col gap-4 mb-4 p-4 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700">
                <select
                    value={selectedRole}
                    onChange={e => setSelectedRole(e.target.value)}
                    className="border p-2 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                >
                    <option value="">Выберите роль</option>
                    {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>

                <input
                    type="number"
                    placeholder="% от выручки"
                    value={percent}
                    onChange={e => handlePositiveNumericChange(e.target.value, setPercent)}
                    min="0" 
                    className="border p-2 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                />

                <input
                    type="number"
                    placeholder="Фикс за смену"
                    value={fixedPerShift}
                    onChange={e => handlePositiveNumericChange(e.target.value, setFixedPerShift)}
                    min="0" 
                    className="border p-2 rounded bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                />

                {/* Цеха */}
                <div>
                    <label className="block mb-1 text-sm font-medium dark:text-gray-300">Цеха</label>
                    {selectedWorkshops.map((w, idx) => (
                        <div key={idx} className="flex gap-2 mb-2">
                            <select
                                value={w ?? ""}
                                onChange={e => {
                                    const newSelected = [...selectedWorkshops];
                                    newSelected[idx] = e.target.value ? Number(e.target.value) : null;
                                    setSelectedWorkshops(newSelected);
                                }}
                                className="border p-2 rounded flex-1 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                            >
                                <option value="">Выберите цех</option>
                                {workshops.map(ws => <option key={ws.id} value={ws.id}>{ws.name}</option>)}
                            </select>
                            <button onClick={() => {
                                const newSelected = [...selectedWorkshops];
                                newSelected.splice(idx, 1);
                                setSelectedWorkshops(newSelected);
                            }} className="bg-red-500 text-white px-2 rounded hover:bg-red-600 dark:hover:bg-red-400">Удалить</button>
                        </div>
                    ))}
                    <button onClick={() => setSelectedWorkshops([...selectedWorkshops, null])}
                        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 dark:hover:bg-blue-400">
                        Ещё цех
                    </button>
                </div>

                {selectedWorkshops.length > 0 && filteredProducts.length > 0 && (
                    <div>
                        <label className="block mb-1 text-sm font-medium dark:text-gray-300">Продукты (за фикс. плату)</label>
                        {selectedProducts.map((p, idx) => (
                            <div key={idx} className="flex gap-2 mb-2">
                                
                                <select
                                
                                    value={p ?? ""}
                                    onChange={e => updateProduct(idx, e.target.value)}
                                    className="border p-2 rounded flex-1 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                                >
                                    <option value="">Выберите продукт</option>
                                    {filteredProducts.map(prod => <option key={prod.id} value={prod.id}>{prod.name}</option>)}
                                </select>
                                <input
                                    type="number"
                                    placeholder="Фикс за товар"
                                    value={p ? fixedPerProduct[p] || "" : ""}
                                    onChange={e => updateFixed(p, e.target.value)}
                                    min="0" 
                                    className="border p-2 rounded w-32 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                                    disabled={!p}
                                />
                                <button onClick={() => removeProduct(idx)} className="bg-red-500 text-white px-2 rounded hover:bg-red-600 dark:hover:bg-red-400">Удалить</button>
                            </div>
                        ))}
                        <button onClick={addProduct} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 dark:hover:bg-blue-400">Ещё продукт</button>
                    </div>
                )}
                
                <div className="flex gap-2 mt-2">
                    <button 
                        onClick={handleSubmit} 
                        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 dark:hover:bg-green-400 flex-1"
                    >
                        {editingRule ? "Сохранить изменения" : "Добавить правило"}
                    </button>
                    {editingRule && (
                        <button 
                            onClick={resetForm} 
                            className="bg-gray-500 text-white rounded hover:bg-gray-600 dark:hover:bg-gray-400 px-4 py-2"
                        >
                            Отмена
                        </button>
                    )}
                </div>
            </div>

            {/* Таблица правил */}
            <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700">
                <table className="w-full text-left">
                    <thead className="border-b dark:border-gray-700">
                        <tr className="bg-gray-100 dark:bg-gray-700">
                            <th className="p-2 font-semibold">Роль</th>
                            <th className="p-2 font-semibold">% от выручки</th>
                            <th className="p-2 font-semibold">Фикс за смену</th>
                            <th className="p-2 font-semibold">Цех</th>
                            {isProductsVisible && <th className="p-2 font-semibold">Продукты и фикс</th>}
                            <th className="p-2 font-semibold">Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {salaryRules.map(r => (
                            <tr key={r.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900">
                                <td className="p-2">{r.role_name ?? r.role ?? "-"}</td>
                                <td className="p-2">{r.percent ?? "-"}</td>
                                <td className="p-2">{r.fixed_per_shift ?? "-"}</td>
                                
                                <td className="p-2">
                                    {Array.isArray(r.workshops) && r.workshops.length > 0
                                    ? r.workshops.map(id => {
                                        const ws = workshops.find(w => w.id === id);
                                        return ws?.name ?? `ID:${id}`; 
                                    }).join(", ") 
                                    : "-"}
                                </td>
                                
                                {isProductsVisible && (
                                    <td className="p-2 text-sm">
                                        {Array.isArray(r.product_fixed) && r.product_fixed.length > 0
                                            ? r.product_fixed.map(pf => (
                                                <div key={pf.product}>
                                                    {pf.product_name ?? `ID:${pf.product}`}: {pf.fixed}
                                                </div>
                                            ))
                                            : "-"}
                                    </td>
                                )}

                                <td className="p-2">
                                    <div className="flex gap-2">
                                        <button 
                                            onClick={() => handleEditClick(r)}
                                            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                            title="Редактировать"
                                        >
                                        Изменить
                                        </button>
                                        <button
                                            onClick={() => handleDeleteRule(r.id)}
                                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                            title="Удалить"
                                        >
                                        Удалить
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}