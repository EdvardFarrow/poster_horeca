from datetime import date, datetime, timedelta

from .client import PosterAPIClient
from .models import CashShiftReport, CategoriesSales, ShiftSale, ShiftSaleItem, Category, Product, Client, Workshop
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed



def save_shift_sales_to_db(api_client, date_str, spot_id=None):
    """
    Сохраняет продажи по сменам в базу.
    Берет данные из метода get_sales_by_shift_with_delivery.
    """
    sales_by_shift = api_client.get_sales_by_shift_with_delivery(date_str, spot_id)

    for shift_id, shift_data in sales_by_shift.items():
        shift_obj, _ = ShiftSale.objects.update_or_create(
            poster_shift_id=shift_id,
            date=date_str,
            defaults={
                'total_revenue': round(sum(item['payed_sum'] for item in shift_data['regular']) +
                                        sum(item['payed_sum'] for item in shift_data['delivery']), 2),
                'total_profit': round(sum(item['profit'] for item in shift_data['regular']) +
                                        sum(item['profit'] for item in shift_data['delivery']), 2),
                'total_percentage': round((sum(item['profit'] for item in shift_data['regular']) +
                                            sum(item['profit'] for item in shift_data['delivery'])) /
                                            (sum(item['payed_sum'] for item in shift_data['regular']) +
                                           sum(item['payed_sum'] for item in shift_data['delivery']) or 1) * 100, 2),
                'total_delivery_revenue': round(sum(item['payed_sum'] for item in shift_data['delivery']), 2),
                'total_delivery_profit': round(sum(item['profit'] for item in shift_data['delivery']), 2),
                'tips': round(shift_data.get('tips', 0.0), 2),
            }
        )

        for category in ['regular', 'delivery']:
            for product in shift_data[category]:
                ShiftSaleItem.objects.update_or_create(
                    shift_sale=shift_obj,
                    product_name=product.get('product_name') or "",
                    defaults={
                        'quantity': product.get('count', 0),
                        'price': product.get('product_sum', 0.0),
                        'paid_sum': product.get('payed_sum', 0.0),
                        'profit': product.get('profit', 0.0),
                        'department': product.get('workshop'),
                        'category_name': category,
                        'delivery_service': product.get('delivery_service') if category == 'delivery' else None
                    }
                )




def save_cash_shifts_range(api_client, start_date: str, end_date: str = None, spot_id: int = None):
    """Сохраняет кассовые смены из API в таблицу CashShiftReport
    для диапазона дат от start_date до end_date (включительно)

    Args:
        api_client (_type_): PosterApiClient
        start_date (str): start_date
        end_date (str, optional): end_date. Defaults to None.
        spot_id (int, optional): spot_id. Defaults to None.
    """
    end_date = end_date or start_date
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    current_date = start_dt
    while current_date <= end_dt:
        date_str = current_date.strftime("%Y-%m-%d")
        shifts = api_client.get_cash_shifts(date_from=date_str, date_to=date_str, spot_id=spot_id)

        for shift in shifts:
            date_start = None
            date_end = None
            try:
                date_start = datetime.strptime(shift['date_start'], "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
            try:
                if shift['date_end'] and shift['date_end'] != '0000-00-00 00:00:00':
                    date_end = datetime.strptime(shift['date_end'], "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

            total_sales = round((shift.get('amount_sell_cash', 0) or 0) + (shift.get('amount_sell_card', 0) or 0), 2)

            CashShiftReport.objects.update_or_create(
                poster_shift_id=shift['poster_shift_id'],
                defaults={
                    'date_start': date_start,
                    'date_end': date_end,
                    'cash_start': shift.get('amount_start', 0),
                    'cash_end': shift.get('amount_end', 0),
                    'amount_debit': shift.get('amount_debit', 0),
                    'amount_sell_cash': shift.get('amount_sell_cash', 0),
                    'amount_sell_card': shift.get('amount_sell_card', 0),
                    'amount_credit': shift.get('amount_credit', 0),
                    'amount_collection': shift.get('amount_collection', 0),
                    'total_sales': total_sales,
                    'comment': shift.get('comment'),
                    'user_id_start': shift.get('user_id_start'),
                    'user_id_end': shift.get('user_id_end'),
                }
            )

        current_date += timedelta(days=1)
        
        
client = PosterAPIClient()
#save_cash_shifts_range(api_client=client, start_date="2023-06-18", end_date="2025-09-13", spot_id=1)


def save_sales_from_august(api_client, spot_id=None):
    """
    Запускает сохранение продаж по сменам
    начиная с 1 августа 2025 года до сегодняшнего дня включительно.
    """
    start_date = date(2025, 8, 1)
    end_date = date.today()

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        save_shift_sales_to_db(api_client, date_str, spot_id)
        current_date += timedelta(days=1)
        




def sync_poster_data(api_client, spot_id=None, max_workers=5):
    """
    Подтягивает категории, продукты, клиентов (с августа 2023 по сегодня)
    и цеха в соответствующие таблицы.
    """

    # --- Categories ---
    categories = api_client.get_category(spot_id=spot_id)
    for c in categories:
        Category.objects.update_or_create(
            category_id=c["category_id"],
            defaults={
                "name": c["name"],
            }
        )

    # --- CategoriesSales ---
    categories_sales = api_client.get_categories_sales(spot_id=spot_id)
    for c in categories_sales:
        CategoriesSales.objects.update_or_create(
            category_id=c["category_id"],  
            defaults={
                "name": c["name"],
                "count": c["count"],
                "profit": c["profit"],
            }
        )


    # --- Products ---
    products = api_client.get_products_sales(spot_id=spot_id)
    for p in products:
        Product.objects.update_or_create(
            name=p["name"],
            defaults={
                "count": p["count"],
                "price": p["price"],
                "product_profit": p["product_profit"],
            }
        )

    # --- Clients (с августа 2023 по сегодня) ---
    start_date = date(2023, 8, 1)
    end_date = date.today()

    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    def fetch_clients(d):
        return d, api_client.get_clients_sales(
            date_from=d.strftime("%Y-%m-%d"),
            date_to=d.strftime("%Y-%m-%d"),
            spot_id=spot_id
        )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_clients, d) for d in dates]
        for future in as_completed(futures):
            d, clients = future.result()
            for cl in clients:
                Client.objects.update_or_create(
                    phone=cl["phone"],
                    date=d,
                    defaults={
                        "firstname": cl.get("firstname"),
                        "lastname": cl.get("lastname"),
                        "email": cl.get("email"),
                        "revenue": cl.get("revenue"),
                        "profit": cl.get("profit"),
                        "transactions": cl.get("transactions"),
                        "avg_check": cl.get("avg_check"),
                        "name": cl.get("name"),
                    }
                )

    # --- Workshops ---
    workshops = api_client.get_payments_id()
    for w in workshops:
        Workshop.objects.update_or_create(
            workshop_id=w["workshop_id"],
            defaults={
                "workshop_name": w["workshop_name"],
                "delete": w["delete"],
            }
        )

    return True