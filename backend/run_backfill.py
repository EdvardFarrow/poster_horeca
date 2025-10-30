import os
import django
from datetime import date, timedelta
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') 
django.setup()


def run_command_for_date(date_str, spot_id, command_name='daily_sync'):
    command = [
        'python',
        'manage.py',
        command_name,
        '--date', date_str,
        '--spot_id', str(spot_id),
        # '--skip-static',  
    ]
    
    print(f"--- Запуск: {' '.join(command)} ---")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
        if result.stderr:
            print(f"[STDERR] {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"!!! ОШИБКА при выполнении команды для {date_str} (Spot {spot_id}) !!!")
        print(e.stdout)
        print(e.stderr)
    except FileNotFoundError:
        print("!!! ОШИБКА: 'python' или 'manage.py' не найдены. Запустите этот скрипт из корня Django-проекта.")
        return False
    except Exception as e:
        print(f"!!! Неизвестная ОШИБКА: {e}")
        return False
        
    return True

def main():
    COMMAND_NAME = 'sync_daily_data' 
    
    SPOT_IDS = [1, 2]
    
    start_date = date(2025, 10, 1)
    end_date = date.today()

    print(f"--- НАЧАЛО БЭКФИЛЛА ---")
    print(f"Команда: {COMMAND_NAME}")
    print(f"Период: {start_date} до {end_date}")
    print(f"Споты: {SPOT_IDS}")
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"=== Обработка даты: {date_str} ===")
        
        for spot_id in SPOT_IDS:
            run_command_for_date(date_str, spot_id, COMMAND_NAME)
            
        current_date += timedelta(days=1)
        
    print("--- БЭКФИЛЛ ЗАВЕРШЕН ---")

if __name__ == "__main__":
    main()