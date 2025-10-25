from collections import defaultdict
from decimal import Decimal
import time
import logging

from shift.models import  Shift, ShiftEmployee
from salary.models import SalaryRule, SalaryRuleProduct
from poster_api.models import ShiftSale, ShiftSaleItem

logger = logging.getLogger(__name__)

def aggregate_sales(shift: Shift):
    start_total = time.time()
    logger.info(f"=== Начало агрегации ЗП для смены {shift.id} (Дата: {shift.date}) ===")

    try:
        shift_sale = ShiftSale.objects.get(shift_id=shift.shift_id)
    except ShiftSale.DoesNotExist:
        logger.error(f"Не найден ShiftSale для shift_id {shift.shift_id}. Расчет невозможен.")
        return {}

    sales_qs = ShiftSaleItem.objects.filter(
        shift_sale=shift_sale,
        category_name='regular'
    )
    logger.info(f"Найдено записей продаж (regular): {sales_qs.count()} "
                f"для ShiftSale {shift_sale.id}")

    sales_agg = defaultdict(lambda: {'sum': Decimal(0), 'count': Decimal(0)})
    workshop_revenue_check = defaultdict(Decimal)
    
    for s in sales_qs:
        key = (s.workshop, s.product_name.strip())
        sale_sum = Decimal(s.payed_sum)
        sales_agg[key]['sum'] += sale_sum
        sales_agg[key]['count'] += Decimal(s.count)
        workshop_revenue_check[s.workshop] += sale_sum

    logger.info(f"Агрегировано {len(sales_agg)} уникальных ключей (цех+продукт)")
    
    logger.info("--- ПРОВЕРКА ВЫРУЧКИ ПО ЦЕХАМ (до применения правил) ---")
    for w_id, total_sum in workshop_revenue_check.items():
        logger.info(f"    Цех ID {w_id}: Общая выручка = {total_sum:.2f}")
    logger.info("------------------------------------------------------")

    role_rules = SalaryRule.objects.prefetch_related('workshops', 'role').all()
    
    all_srp = SalaryRuleProduct.objects.select_related('product').all()

    srp_map = defaultdict(dict)
    for srp in all_srp:
        srp_map[srp.salary_rule_id][srp.product.product_name.strip()] = Decimal(srp.fixed or 0)

    logger.info(f"Всего правил ЗП загружено: {len(role_rules)}")
    logger.info(f"Всего бонусных продуктов загружено: {len(all_srp)}")

    shift_employees = ShiftEmployee.objects.filter(
        shift=shift
    ).select_related(
        "employee", 
        "role", 
        "role__pay_group"
    )

    employees_by_role_id = defaultdict(list)
    employees_by_pay_group = defaultdict(list) 
    role_map = {}

    for se in shift_employees:
        employees_by_role_id[se.role_id].append(se.employee)
        
        if se.role_id not in role_map:
            role_map[se.role_id] = se.role
        
        pay_group_id = se.role.pay_group_id
        
        if pay_group_id:
            employees_by_pay_group[pay_group_id].append(se)
        else:
            employees_by_pay_group[f"role_{se.role_id}"].append(se)

    logger.info(f"Сотрудников на смене: {len(shift_employees)}")
    for role_id, emps in employees_by_role_id.items():
        role_name = role_map[role_id].name
        emp_names = [e.name for e in emps]
        logger.info(f"Роль {role_id} ({role_name}): {len(emps)} сотр. -> {emp_names}")

    result = {}
    for role_id, employees in employees_by_role_id.items():
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
            logger.info(f"Сотрудник {emp.name} (ID {emp.id}) "
                        f"получил фикс {fixed_per_shift} -> "
                        f"total_salary={fixed_per_shift}")

    for group_key, shift_employees_in_group in employees_by_pay_group.items():
        
        total_percent_for_group = Decimal(0)
        total_bonus_for_group = Decimal(0)
        bonus_breakdown_map = defaultdict(lambda: {'count': Decimal(0), 'total': Decimal(0)})

        role_ids_in_group = {se.role_id for se in shift_employees_in_group}
        rules_for_this_group = [r for r in role_rules if r.role_id in role_ids_in_group]
        
        if not rules_for_this_group:
            continue

        group_name = f"Role {role_ids_in_group}"
        if isinstance(group_key, int):
            first_role = role_map[list(role_ids_in_group)[0]]
            if first_role.pay_group:
                group_name = f"PayGroup '{first_role.pay_group.name}'"

        logger.info(f"--- Расчет для группы: {group_name} (Ключ: {group_key}) ---")
        logger.info(f"    Сотрудники в группе: {[se.employee.name for se in shift_employees_in_group]}")
        logger.info(f"    Активные правила: {[r.id for r in rules_for_this_group]}")
        
        for rule in rules_for_this_group:
            
            percent = Decimal(rule.percent or 0) / 100
            rule_workshops_ids = {w.id for w in rule.workshops.all()} 
            bonuses_for_this_rule = srp_map.get(rule.id, {})
            rule_products_names = set(bonuses_for_this_rule.keys())
            
            if percent > 0 or bonuses_for_this_rule:
                logger.info(f"  Применяем правило {rule.id} (Роль: {rule.role.name})")
                
                for (w_id_str, product_name), sale_data in sales_agg.items():
                    try:
                        w_id_int = int(w_id_str) 
                    except (ValueError, TypeError):
                        continue
                    
                    if w_id_int not in rule_workshops_ids:
                        continue
                    
                    product_sum = sale_data["sum"]
                    item_count = sale_data["count"]

                    if percent > 0:
                        total_percent_for_group += product_sum * percent

                    if product_name in rule_products_names:
                        bonus_per_item = bonuses_for_this_rule.get(product_name, Decimal(0))
                        if bonus_per_item > 0:
                            item_count = sale_data["count"]
                            total_bonus_for_product = item_count * bonus_per_item
                            total_bonus_for_group += item_count * bonus_per_item
                            
                            breakdown = bonus_breakdown_map[product_name]
                            breakdown['count'] += item_count
                            breakdown['total'] += total_bonus_for_product

        logger.info(f"--- Итого для группы {group_name} (до 'костыля'): "
                    f"Начислено % = {total_percent_for_group:.2f}. "
                    f"Начислено бонусов = {total_bonus_for_group:.2f} ---")
        
        if total_percent_for_group > 0 or total_bonus_for_group > 0:
            
            splitting_employees_list = [se.employee for se in shift_employees_in_group]
            num_to_split_between = len(splitting_employees_list)

            if num_to_split_between == 0:
                continue

            if isinstance(group_key, int):
                logger.info(f" PayGroup: делим банк {num_to_split_between} раз.")
                total_percent_for_group = total_percent_for_group / num_to_split_between
                total_bonus_for_group = total_bonus_for_group / num_to_split_between
                for product_name in bonus_breakdown_map:
                    bonus_breakdown_map[product_name]['total'] /= num_to_split_between
            else:
                logger.info(f" Стандартная роль.")

            percent_per_employee = total_percent_for_group / num_to_split_between
            bonus_per_employee = total_bonus_for_group / num_to_split_between
            final_bonus_breakdown = [
                {'product_name': name, 'count': data['count'], 'total': data['total']}
                for name, data in bonus_breakdown_map.items()
            ]
            
            logger.info(f"  Делим {total_percent_for_group:.2f} % и {total_bonus_for_group:.2f} бонусов "
                        f"на {num_to_split_between} чел. = "
                        f"{percent_per_employee:.2f} / {bonus_per_employee:.2f} на каждого.")

            for emp in splitting_employees_list:
                emp_key = emp.id
                result[emp_key]["total_salary"] += percent_per_employee + bonus_per_employee
                result[emp_key]["percent_total"] += percent_per_employee
                result[emp_key]["fixed_bonus_total"] += bonus_per_employee
                
                result[emp_key]["details"]["percent"] = result[emp_key]["percent_total"]
                result[emp_key]["details"]["bonus"] = result[emp_key]["fixed_bonus_total"]
                result[emp_key]["details"]["bonus_breakdown"] = final_bonus_breakdown
                
                logger.info(
                    f"  -> Сотрудник {emp.name} (ID {emp.id}): "
                    f"начислено {percent_per_employee:.2f} + {bonus_per_employee:.2f}"
                )
    
    logger.info("--- ИТОГОВЫЙ РАСЧЕТ ПО СОТРУДНИКАМ ---")
    for emp_id, data in result.items():
        total = data["total_salary"]
        logger.info(
            f"ИТОГ Сотрудник {data['employee'].name} (ID {emp_id}): "
            f"фикс {data['details'].get('fixed', 0):.2f}, "
            f"процент {data['percent_total']:.2f}, "
            f"бонус {data['fixed_bonus_total']:.2f} -> "
            f"ИТОГО {total:.2f}"
        )

    logger.info(f"=== Конец агрегации для смены {shift.id} (время: {round(time.time()-start_total, 2)} сек) ===")
    return result