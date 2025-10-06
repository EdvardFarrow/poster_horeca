from collections import defaultdict
from shift.models import Shift
from users.models import Employee
from salary.models import SalaryRule, SalaryRuleProduct
from poster_api.models import Product, ShiftSale, ShiftSaleItem
from decimal import Decimal
import time
import logging

logger = logging.getLogger(__name__)



def aggregate_sales(shift: Shift):

    start_total = time.time()
    logger.info(f"=== Начало агрегации продаж для смены {shift.id} ===")

    # --- 1. Загружаем продукты ---
    products = Product.objects.all()
    product_map = {p.product_name.strip(): p for p in products}
    logger.info(f"Продуктов загружено: {len(product_map)}")

    # --- 2. Загружаем продажи по этой смене ---
    sales_qs = ShiftSaleItem.objects.filter(
        shift_sale__shift_id=shift.id
    ).select_related('shift_sale')
    logger.info(f"Продаж загружено: {sales_qs.count()}")

    # --- 3. Фильтруем продажи по продуктам ---
    sales = []
    for s in sales_qs:
        product_name = s.product_name.strip()
        product = product_map.get(product_name)
        if not product:
            logger.warning(f"Продукт '{product_name}' не найден, пропуск.")
            continue
        sales.append({
            'product_id': product.id,
            'workshop_id': product.workshop.id,
            'product_sum': Decimal(s.product_sum),
            'count': s.count
        })

    # --- 4. Агрегируем продажи по (workshop, product) ---
    sales_agg = defaultdict(lambda: {'sum': Decimal(0), 'count': 0})
    for sale in sales:
        key = (sale['workshop_id'], sale['product_id'])
        sales_agg[key]['sum'] += sale['product_sum']
        sales_agg[key]['count'] += sale['count']
    logger.info(f"Агрегировано {len(sales_agg)} уникальных ключей (цех+продукт)")

    # --- 5. Загружаем все правила и фиксированные бонусы заранее ---
    role_rules = SalaryRule.objects.prefetch_related('products', 'workshops').all()
    all_srp = SalaryRuleProduct.objects.all().select_related('product')
    srp_map = defaultdict(dict)
    for srp in all_srp:
        srp_map[srp.salary_rule_id][srp.product_id] = Decimal(srp.fixed or 0)

    # --- 6. Группируем сотрудников по ролям ---
    shift_employees = shift.shiftemployee_set.select_related('employee', 'role')
    employees_by_role = defaultdict(list)
    for se in shift_employees:
        employees_by_role[se.role_id].append(se.employee)

    # --- 7. Расчёт зарплаты ---
    result = {}
    for role_id, employees in employees_by_role.items():
        num_employees = len(employees) or 1
        logger.debug(f"Роль {role_id} имеет {num_employees} сотрудников на смене")

        role_rule_list = [r for r in role_rules if r.role_id == role_id]
        for rule in role_rule_list:
            rule_products = [p.id for p in rule.products.all()]
            rule_workshops = [w.id for w in rule.workshops.all()]
            percent = Decimal(rule.percent or 0) / 100
            fixed_per_shift = Decimal(rule.fixed_per_shift or 0)

            for workshop_id in rule_workshops:
                for product_id in rule_products:
                    sale_data = sales_agg.get((workshop_id, product_id))
                    if not sale_data:
                        continue

                    # фикс и процент делим на количество сотрудников этой роли
                    percent_bonus = (sale_data['sum'] * percent) / num_employees
                    fixed_bonus = srp_map.get(rule.id, {}).get(product_id, Decimal(0)) / num_employees

                    for emp in employees:
                        if emp.id not in result:
                            result[emp.id] = {'employee': emp, 'total_salary': Decimal(0)}
                        result[emp.id]['total_salary'] += percent_bonus + fixed_bonus

            # Добавляем фикс за смену (делим на количество сотрудников роли)
            for emp in employees:
                result[emp.id]['total_salary'] += fixed_per_shift / num_employees

    # Округляем суммы
    for emp_id, data in result.items():
        data['total_salary'] = round(data['total_salary'], 2)

    logger.info(f"=== Конец агрегации для смены {shift.id} (время: {time.time() - start_total:.2f} сек) ===")
    return result