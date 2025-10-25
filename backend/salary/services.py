from decimal import Decimal
from .models import SalaryRecord
from .aggreg import aggregate_sales
import logging

logger = logging.getLogger(__name__)

def calculate_and_save_shift_salaries(shift):
    logger.info(f"Вызов calculate_and_save_shift_salaries для смены {shift.id}")
    
    salary_data = aggregate_sales(shift)
    
    for emp_id, data in salary_data.items():
        old_record = SalaryRecord.objects.filter(employee_id=emp_id, shift=shift).first()
        old_details = old_record.details if old_record and old_record.details else {}

        new_calculated_details = data['details']
        
        manual_details = {
            'write_off': old_details.get('write_off', 0),
            'comment': old_details.get('comment', '')
        }
        
        final_details = {**manual_details, **new_calculated_details}
        
        fixed = Decimal(final_details.get('fixed', 0))
        percent = Decimal(final_details.get('percent', 0))
        bonus = Decimal(final_details.get('bonus', 0))
        write_off = Decimal(final_details.get('write_off', 0))
        
        total_salary = fixed + percent + bonus - write_off

        json_safe_details = {
            'fixed': float(fixed),
            'percent': float(percent),
            'bonus': float(bonus),
            'write_off': float(write_off),
            'comment': final_details.get('comment', ''),
            'bonus_breakdown': [
                {
                    'product_name': item['product_name'],
                    'count': float(item['count']),
                    'total': float(item['total'])
                } for item in final_details.get('bonus_breakdown', [])
            ]
        }

        SalaryRecord.objects.update_or_create(
            employee_id=emp_id, 
            shift=shift,
            defaults={
                'total_salary': total_salary,
                'details': json_safe_details,
                
                'fixed_part': fixed,
                'percent_part': percent,
                'bonus_part': bonus,
                'write_off': write_off,
                'comment': final_details.get('comment', '')
            }
        )
    logger.info(f"ЗП для смены {shift.id} сохранена.")