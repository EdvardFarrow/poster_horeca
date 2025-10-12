from .models import SalaryRecord
from .aggreg import aggregate_sales 

def calculate_and_save_shift_salaries(shift):
    
    salary_results = aggregate_sales(shift)

    for emp_id, data in salary_results.items():
        SalaryRecord.objects.update_or_create(
            employee_id=emp_id,
            shift=shift,
            defaults={
                'total_salary': data.get("total_salary", 0),
                'fixed_part': data["details"].get("fixed", 0),
                'percent_part': data.get("percent_total", 0),
                'bonus_part': data.get("fixed_bonus_total", 0),
            }
        )
    
    print(f"Зарплаты для смены {shift.id} от {shift.date} были рассчитаны и сохранены.")
    return salary_results