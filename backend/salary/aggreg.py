from collections import defaultdict
from decimal import Decimal
import time
import logging

from shift.models import  ShiftEmployee
from salary.models import SalaryRule, SalaryRuleProduct
from poster_api.models import ShiftSaleItem

logger = logging.getLogger(__name__)

def aggregate_sales(shift):
    start_total = time.time()
    logger.info(f"=== Начало агрегации продаж для смены {shift.id} (shift_id={shift.shift_id}) ===")

    # Загружаем все продажи за смену 
    sales_qs = ShiftSaleItem.objects.filter(shift_sale__shift_id=shift.shift_id)
    logger.info(f"Всего записей продаж найдено: {sales_qs.count()}")

    # Агрегируем продажи по (workshop_id, product_name) 
    sales_agg = defaultdict(lambda: {'sum': Decimal(0), 'count': 0})
    for s in sales_qs:
        product_name = s.product_name.strip()
        key = (s.workshop, product_name)
        sales_agg[key]['sum'] += Decimal(s.product_sum)
        sales_agg[key]['count'] += s.count

    logger.info(f"Агрегировано {len(sales_agg)} уникальных ключей (цех+продукт)")
    for key, data in list(sales_agg.items())[:5]:
        logger.debug(f"Пример ключа {key}: sum={data['sum']}, count={data['count']}")

    # Загружаем правила зарплаты 
    role_rules = SalaryRule.objects.prefetch_related('products', 'workshops').all()
    all_srp = SalaryRuleProduct.objects.all().select_related('product')

    srp_map = defaultdict(dict)
    for srp in all_srp:
        srp_map[srp.salary_rule_id][srp.product.product_name.strip()] = Decimal(srp.fixed or 0)

    logger.info(f"Всего правил зарплаты загружено: {len(role_rules)}")
    logger.info(f"Всего фиксированных бонусов загружено: {len(all_srp)}")
    
    for rule in role_rules:
        role_id = rule.role_id
        role_name = getattr(rule.role, "name", f"Role {role_id}")
        workshops = [w.id for w in rule.workshops.all()]
        products = [p.product_name.strip() for p in rule.products.all()]
        percent = Decimal(rule.percent or 0)
        fixed_per_shift = Decimal(rule.fixed_per_shift or 0)
        
        logger.info(
            f"Правило для роли {role_name} (ID {role_id}): "
            f"фикс={fixed_per_shift}, процент={percent}%, "
            f"цеха={workshops}, продукты={products}"
        )

    # Лог фиксированных бонусов по продуктам
    for rule_id, products_map in srp_map.items():
        logger.info(f"Фиксированные бонусы для SalaryRule {rule_id}: {products_map}")

    # Группируем сотрудников по ролям 
    shift_employees = ShiftEmployee.objects.filter(shift=shift).select_related("employee")
    employees_by_role = defaultdict(list)
    for se in shift_employees:
        employees_by_role[se.role_id].append(se.employee)

    logger.info(f"Сотрудников на смене: {len(shift_employees)}")
    for role_id, emps in employees_by_role.items():
        emp_ids = [e.id for e in emps]
        emp_names = [e.name for e in emps]
        logger.info(f"Роль {role_id}: {len(emps)} сотрудников -> IDs: {emp_ids}, Names: {emp_names}")

    # Инициализация результата с фиксами 
    result = {}
    for role_id, employees in employees_by_role.items():
        role_rule_list = [r for r in role_rules if r.role_id == role_id]
        for emp in employees:
            fixed_per_shift = sum(Decimal(r.fixed_per_shift or 0) for r in role_rule_list)
            result[emp.id] = {
                "employee": emp,
                "total_salary": fixed_per_shift,
                "details": {"fixed": fixed_per_shift},
                "percent_total": Decimal(0),
                "fixed_bonus_total": Decimal(0),
            }
            logger.info(f"Сотрудник {emp.name} (ID {emp.id}) получил фикс {fixed_per_shift} -> total_salary={fixed_per_shift}")

    # Начисляем проценты и бонусы по продажам 
    for rule in role_rules:
        if rule.role_id not in employees_by_role:
            continue

        employees = employees_by_role[rule.role_id]
        num_employees = len(employees)
        if num_employees == 0:
            continue
        
        # Считаем общую сумму по правилу
        total_percent_for_rule = Decimal(0)
        total_bonus_for_rule = Decimal(0)

        percent = Decimal(rule.percent or 0) / 100
        rule_workshops = {w.id for w in rule.workshops.all()} 
        rule_products = {p.product_name.strip() for p in rule.products.all()}

        # Расчет общего процента по правилу
        if percent > 0 and rule_workshops:
            for (w_id, product_name), sale_data in sales_agg.items():
                if int(w_id) in rule_workshops:
                    total_percent_for_rule += sale_data["sum"] * percent
        
        # Расчет общего бонуса по правилу
        if rule_products:
            bonuses_for_this_rule = srp_map.get(rule.id, {})
            if bonuses_for_this_rule:
                for (w_id, product_name), sale_data in sales_agg.items():
                    if int(w_id) in rule_workshops and product_name in rule_products:
                        bonus_per_item = bonuses_for_this_rule.get(product_name, Decimal(0))
                        total_bonus_for_rule += sale_data["count"] * bonus_per_item

        # Делим общую сумму на всех сотрудников этой роли 
        if total_percent_for_rule > 0 or total_bonus_for_rule > 0:
            percent_per_employee = total_percent_for_rule / num_employees
            bonus_per_employee = total_bonus_for_rule / num_employees

            # Начисляем каждому сотруднику его долю
            for emp in employees:
                emp_key = emp.id
                result[emp_key]["total_salary"] += percent_per_employee + bonus_per_employee
                result[emp_key]["percent_total"] += percent_per_employee
                result[emp_key]["fixed_bonus_total"] += bonus_per_employee
                
                # Обновляем детализацию
                result[emp_key]["details"]["percent"] = result[emp_key]["percent_total"]
                result[emp_key]["details"]["bonus"] = result[emp_key]["fixed_bonus_total"]
                
                logger.info(
                    f"Сотрудник {emp.name} (ID {emp.id}) по правилу {rule.id}: "
                    f"начислено процента {percent_per_employee:.2f}, бонуса {bonus_per_employee:.2f}"
                )

    # Итог
    for emp_id, data in result.items():
        total = data["total_salary"]
        
        logger.info(
            f"ИТОГ Сотрудник {data['employee'].name} (ID {emp_id}): "
            f"фикс {data['details'].get('fixed', 0):.2f}, "
            f"процент {data['percent_total']:.2f}, "
            f"бонус {data['fixed_bonus_total']:.2f} -> "
            f"итого {total:.2f}"
        )

    logger.info(f"=== Конец агрегации для смены {shift.id} (время: {round(time.time()-start_total, 2)} сек) ===")
    return result
