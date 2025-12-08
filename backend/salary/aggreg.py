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
    logger.info(f"=== Starting salary aggregation for shift {shift.id} (Date: {shift.date}) ===")

    try:
        shift_sale = ShiftSale.objects.get(shift_id=shift.shift_id)
    except ShiftSale.DoesNotExist:
        logger.error(f"ShiftSale not found for shift_id {shift.shift_id}. Calculation impossible.")
        return {}

    sales_qs = ShiftSaleItem.objects.filter(
        shift_sale=shift_sale,
        category_name='regular'
    )
    logger.info(f"Found sales records (regular): {sales_qs.count()} "
                f"for ShiftSale {shift_sale.id}")

    sales_agg = defaultdict(lambda: {'sum': Decimal(0), 'count': Decimal(0)})
    workshop_revenue_check = defaultdict(Decimal)
    
    for s in sales_qs:
        key = (s.workshop, s.product_name.strip())
        sale_sum = Decimal(s.payed_sum)
        sales_agg[key]['sum'] += sale_sum
        sales_agg[key]['count'] += Decimal(s.count)
        workshop_revenue_check[s.workshop] += sale_sum

    logger.info(f"Aggregated {len(sales_agg)} unique keys (workshop+product)")
    
    logger.info("--- WORKSHOP REVENUE CHECK (before applying rules) ---")
    for w_id, total_sum in workshop_revenue_check.items():
        logger.info(f"    Workshop ID {w_id}: Total revenue = {total_sum:.2f}")
    logger.info("------------------------------------------------------")

    role_rules = SalaryRule.objects.prefetch_related('workshops', 'role').all()
    
    all_srp = SalaryRuleProduct.objects.select_related('product').all()

    srp_map = defaultdict(dict)
    for srp in all_srp:
        srp_map[srp.salary_rule_id][srp.product.product_name.strip()] = Decimal(srp.fixed or 0)

    logger.info(f"Total salary rules loaded: {len(role_rules)}")
    logger.info(f"Total bonus products loaded: {len(all_srp)}")

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

    logger.info(f"Employees on shift: {len(shift_employees)}")
    for role_id, emps in employees_by_role_id.items():
        role_name = role_map[role_id].name
        emp_names = [e.name for e in emps]
        logger.info(f"Role {role_id} ({role_name}): {len(emps)} empl. -> {emp_names}")

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
            logger.info(f"Employee {emp.name} (ID {emp.id}) "
                        f"received fixed {fixed_per_shift} -> "
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

        logger.info(f"--- Calculation for group: {group_name} (Key: {group_key}) ---")
        logger.info(f"    Employees in group: {[se.employee.name for se in shift_employees_in_group]}")
        logger.info(f"    Active rules: {[r.id for r in rules_for_this_group]}")
        
        prepped_rules = []
        for r in rules_for_this_group:
            prepped_rules.append({
                'rule': r,
                'percent': Decimal(r.percent or 0) / 100,
                'workshops': {w.id for w in r.workshops.all()},
                'bonus_products': srp_map.get(r.id, {})
            })

        for (w_id_str, product_name), sale_data in sales_agg.items():
            try:
                w_id_int = int(w_id_str) 
            except (ValueError, TypeError):
                continue

            product_sum = sale_data["sum"]
            item_count = sale_data["count"]

            count_added_to_breakdown = False

            for p_rule in prepped_rules:
                
                if w_id_int not in p_rule['workshops']:
                    continue
                
                if p_rule['percent'] > 0:
                    total_percent_for_group += product_sum * p_rule['percent']

                bonus_per_item = p_rule['bonus_products'].get(product_name, Decimal(0))
                
                if bonus_per_item > 0:
                    total_bonus_for_product = item_count * bonus_per_item
                    total_bonus_for_group += total_bonus_for_product
                    
                    breakdown = bonus_breakdown_map[product_name]
                    
                    if not count_added_to_breakdown:
                        breakdown['count'] += item_count
                        count_added_to_breakdown = True 
                    
                    breakdown['total'] += total_bonus_for_product

        logger.info(f"--- Total for group {group_name}: "
                    f"Accrued % = {total_percent_for_group:.2f}. "
                    f"Accrued bonuses = {total_bonus_for_group:.2f} ---")
        
        if total_percent_for_group > 0 or total_bonus_for_group > 0:
            
            splitting_employees_list = [se.employee for se in shift_employees_in_group]
            num_to_split_between = len(splitting_employees_list)

            if num_to_split_between == 0:
                continue

            # if isinstance(group_key, int):
            #     logger.info(f" PayGroup: splitting pot {num_to_split_between} times.")
            #     total_percent_for_group = total_percent_for_group / num_to_split_between
            #     total_bonus_for_group = total_bonus_for_group / num_to_split_between
            #     for product_name in bonus_breakdown_map:
            #          bonus_breakdown_map[product_name]['total'] /= num_to_split_between
            # else:
            #     logger.info(f" Standard role.")

            percent_per_employee = total_percent_for_group / num_to_split_between
            bonus_per_employee = total_bonus_for_group / num_to_split_between
            
            final_bonus_breakdown = [
                {'product_name': name, 'count': data['count'], 'total': data['total']}
                for name, data in bonus_breakdown_map.items()
            ]
            
            logger.info(f"  Splitting {total_percent_for_group:.2f} % and {total_bonus_for_group:.2f} bonuses "
                        f"among {num_to_split_between} people = "
                        f"{percent_per_employee:.2f} / {bonus_per_employee:.2f} each.")

            for emp in splitting_employees_list:
                emp_key = emp.id
                result[emp_key]["total_salary"] += percent_per_employee + bonus_per_employee
                result[emp_key]["percent_total"] += percent_per_employee
                result[emp_key]["fixed_bonus_total"] += bonus_per_employee
                
                result[emp_key]["details"]["percent"] = result[emp_key]["percent_total"]
                result[emp_key]["details"]["bonus"] = result[emp_key]["fixed_bonus_total"]
                result[emp_key]["details"]["bonus_breakdown"] = final_bonus_breakdown
                
                logger.info(
                    f"  -> Employee {emp.name} (ID {emp.id}): "
                    f"accrued {percent_per_employee:.2f} + {bonus_per_employee:.2f}"
                )
    
    logger.info("--- FINAL CALCULATION BY EMPLOYEES ---")
    for emp_id, data in result.items():
        total = data["total_salary"]
        logger.info(
            f"RESULT Employee {data['employee'].name} (ID {emp_id}): "
            f"fixed {data['details'].get('fixed', 0):.2f}, "
            f"percent {data['percent_total']:.2f}, "
            f"bonus {data['fixed_bonus_total']:.2f} -> "
            f"TOTAL {total:.2f}"
        )

    logger.info(f"=== End of aggregation for shift {shift.id} (time: {round(time.time()-start_total, 2)} sec) ===")
    return result
