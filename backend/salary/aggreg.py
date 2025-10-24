from collections import defaultdict
from decimal import Decimal
import time
import logging

from shift.models import  ShiftEmployee
from salary.models import SalaryRule, SalaryRuleProduct
from poster_api.models import ShiftSaleItem

logger = logging.getLogger(__name__)

def aggregate_sales(shift):
    """Calculates the total salary for all employees on a given shift.
    ... (docstring) ...
    """
    start_total = time.time()
    logger.info(f"=== Начало агрегации продаж для смены {shift.id} (shift_id={shift.shift_id}) ===")

    sales_qs = ShiftSaleItem.objects.filter(
        shift_sale__shift_id=shift.shift_id,
        category_name='regular'  
    )
    logger.info(f"Всего записей продаж найдено (только 'Зал'): {sales_qs.count()}")

    workshop_revenue_check = defaultdict(Decimal)
    
    sales_agg = defaultdict(lambda: {'sum': Decimal(0), 'count': 0})
    for s in sales_qs:
        product_name = s.product_name.strip()
        key = (s.workshop, product_name)
        
        sale_sum = Decimal(s.payed_sum) 
        
        sales_agg[key]['sum'] += sale_sum
        sales_agg[key]['count'] += s.count
        
        workshop_revenue_check[s.workshop] += sale_sum

    logger.info(f"Агрегировано {len(sales_agg)} уникальных ключей (цех+продукт)")
    
    logger.info("--- ПРОВЕРКА ВЫРУЧКИ ПО ЦЕХАМ (до применения правил) ---")
    for w_id, total_sum in workshop_revenue_check.items():
        logger.info(f"    Цех ID {w_id}: Общая выручка = {total_sum:.2f}")
    logger.info("------------------------------------------------------")


    role_rules = SalaryRule.objects.prefetch_related('products', 'workshops').all()
    
    all_srp = SalaryRuleProduct.objects.prefetch_related('product').all()


    srp_map = defaultdict(dict)
    for srp in all_srp:
        srp_map[srp.salary_rule_id][srp.product.product_name.strip()] = Decimal(srp.fixed or 0)

    logger.info(f"Всего правил зарплаты загружено: {len(role_rules)}")
    logger.info(f"Всего фиксированных бонусов загружено: {len(all_srp)}")
    
    shift_employees = ShiftEmployee.objects.filter(shift=shift).select_related("employee")
    employees_by_role = defaultdict(list)
    for se in shift_employees:
        employees_by_role[se.role_id].append(se.employee)

    logger.info(f"Сотрудников на смене: {len(shift_employees)}")
    for role_id, emps in employees_by_role.items():
        emp_names = [e.name for e in emps]
        logger.info(f"Роль {role_id}: {len(emps)} сотрудников -> {emp_names}")


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


    for rule in role_rules:
        if rule.role_id not in employees_by_role:
            continue

        employees = employees_by_role[rule.role_id]
        num_employees = len(employees)
        if num_employees == 0:
            continue
        
        total_percent_for_rule = Decimal(0)
        total_bonus_for_rule = Decimal(0)

        percent = Decimal(rule.percent or 0) / 100
        rule_workshops = {w.id for w in rule.workshops.all()} 
        rule_products = {p.product_name.strip() for p in rule.products.all()}

        if percent > 0 and rule_workshops:
            
            logger.info(f"--- Расчет % для правила {rule.id} (Роль: {rule.role.name}, Цеха: {rule_workshops}) ---")
            total_revenue_for_this_rule = Decimal(0)
            
            for (w_id, product_name), sale_data in sales_agg.items():
                if int(w_id) in rule_workshops:
                    
                    product_sum = sale_data["sum"] 
                    logger.info(f"  [+] Добавляем: Цех {w_id}, Продукт '{product_name}', Сумма {product_sum:.2f}")
                    
                    total_revenue_for_this_rule += product_sum
                    total_percent_for_rule += product_sum * percent
            
            logger.info(f"--- Итого для правила {rule.id}: Общая выручка = {total_revenue_for_this_rule:.2f}. "
                        f"Начислено % (до деления) = {total_percent_for_rule:.2f} ---")

        
        if rule_products:
            bonuses_for_this_rule = srp_map.get(rule.id, {})
            if bonuses_for_this_rule:
                
                logger.info(f"--- Расчет бонусов для правила {rule.id} (Продукты: {rule_products}) ---")
                
                for (w_id, product_name), sale_data in sales_agg.items():
                    if int(w_id) in rule_workshops and product_name in rule_products:
                        bonus_per_item = bonuses_for_this_rule.get(product_name, Decimal(0))
                        if bonus_per_item > 0:
                            item_count = sale_data["count"]
                            total_bonus_for_product = item_count * bonus_per_item
                            total_bonus_for_rule += total_bonus_for_product
                            logger.info(f"  [+] Бонус: Продукт '{product_name}', {item_count} шт * {bonus_per_item} = {total_bonus_for_product:.2f}")

                logger.info(f"--- Итого бонусов для правила {rule.id} = {total_bonus_for_rule:.2f} ---")


        if total_percent_for_rule > 0 or total_bonus_for_rule > 0:
            percent_per_employee = total_percent_for_rule / num_employees
            bonus_per_employee = total_bonus_for_rule / num_employees

            for emp in employees:
                emp_key = emp.id
                result[emp_key]["total_salary"] += percent_per_employee + bonus_per_employee
                result[emp_key]["percent_total"] += percent_per_employee
                result[emp_key]["fixed_bonus_total"] += bonus_per_employee
                
                result[emp_key]["details"]["percent"] = result[emp_key]["percent_total"]
                result[emp_key]["details"]["bonus"] = result[emp_key]["fixed_bonus_total"]
                
                logger.info(
                    f"Сотрудник {emp.name} (ID {emp.id}) по правилу {rule.id}: "
                    f"начислено процента {percent_per_employee:.2f}, бонуса {bonus_per_employee:.2f}"
                )
    
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

