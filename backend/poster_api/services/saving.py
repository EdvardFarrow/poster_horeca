import asyncio
from decimal import Decimal
from asgiref.sync import sync_to_async
from datetime import date, datetime, timedelta
from django.utils import timezone
import json
import logging
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime


from ..serializers import (
    CategoriesSalesAPISerializer, 
    CategoryAPISerializer,
    PaymentMethodSerializer, 
    ProductAPISerializer, 
    ProductSalesAPISerializer,
    WorkshopSerializer
)
from ..models import (
    CashShiftReport, 
    CategoriesSales,
    Payments_ID,
    ProductSales, 
    ShiftSale, 
    ShiftSaleItem, 
    Category,
    Product, 
    Clients,
    TransactionHistory,
    TransactionsProducts, 
    Workshop, 
    Transactions
    )
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from rest_framework.exceptions import ValidationError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_shift_sales_to_db(api_client, date_str, spot_id=None):
    """
    Сохраняет продажи по сменам в базу.
    Берет данные из метода get_sales_by_shift_with_delivery.
    """
    sales_by_shift = api_client.get_sales_by_shift_with_delivery(date_str, spot_id)

    for shift_id, shift_data in sales_by_shift.items():
        shift_obj, _ = ShiftSale.objects.update_or_create(
            shift_id=shift_id,
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
                logger.info(f"Processing shift_id={shift_id}, product_name={product.get('product_name')}, "
                            f"workshop={product.get('workshop')}, category={category}, "
                            f"delivery_service={product.get('delivery_service')}, tips={product.get('tips')}")
                
                try:
                    ShiftSaleItem.objects.update_or_create(
                        shift_sale=shift_obj,
                        product_name=product.get('product_name') or "",
                        defaults={
                            'count': product.get('count', 0),
                            'product_sum': product.get('product_sum', 0.0),
                            'payed_sum': product.get('payed_sum', 0.0),
                            'profit': product.get('profit', 0.0),
                            'workshop': product.get('workshop'),
                            'category_name': category,
                            'delivery_service': product.get('delivery_service') if category == 'delivery' else None,
                            'tips': product.get('tips', 0.0),
                        }
                    )
                except Exception as e:
                    logger.error(f"❌ Error saving ShiftSaleItem for shift_id={shift_id}, "
                                f"product_name={product.get('product_name')}, error={e}")
                    continue




def save_cash_shifts_range(api_client, start_date: str, spot_id: int = None, end_date: str = None):
    """Сохраняет кассовые смены из API в таблицу CashShiftReport
    для диапазона дат от start_date до end_date (включительно)

    Args:
        api_client (_type_): PosterApiClient
        start_date (str): start_date
        end_date (str, optional): end_date. Defaults to None.
        spot_id (int, optional): spot_id. Defaults to None.
    """
    end_date = end_date or start_date
    start_dt = datetime.strptime(str(start_date), "%Y-%m-%d")
    end_dt = datetime.strptime(str(end_date), "%Y-%m-%d")

    current_date = start_dt
    while current_date <= end_dt:
        date_str = current_date.strftime("%Y-%m-%d")
        shifts = api_client.get_cash_shifts(date_from=date_str, date_to=date_str, spot_id=spot_id)

        for shift in shifts:
            date_start = None
            date_end = None

            # Обработка даты начала смены
            try:
                date_start_naive = datetime.strptime(shift['date_start'], "%Y-%m-%d %H:%M:%S")
                date_start = timezone.make_aware(date_start_naive, timezone.get_current_timezone())
            except Exception:
                pass

            # Обработка даты конца смены
            try:
                if shift.get('date_end') and shift['date_end'] != '0000-00-00 00:00:00':
                    date_end_naive = datetime.strptime(shift['date_end'], "%Y-%m-%d %H:%M:%S")
                    date_end = timezone.make_aware(date_end_naive, timezone.get_current_timezone())
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




def save_sales_from_september(api_client, spot_id=None):
    """
    Запускает сохранение продаж по сменам
    начиная с 1 сентября 2025 года до сегодняшнего дня включительно.
    """
    start_date = date(2025, 10, 1)
    end_date = date(2025, 10, 1)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        try:
            save_shift_sales_to_db(api_client, date_str)
            save_cash_shifts_range(api_client, date_str)
            logger.info(f"✅ Data for {date_str} successfully saved to DB")
        except Exception as e:
            logger.error(f"❌ Error saving data for {date_str}: {e}")
        current_date += timedelta(days=1)






def save_products(products_data: list[dict]):
    """
    Сохраняет список продуктов в таблицу Product через сериализатор.
    """
    serializer = ProductAPISerializer(data=products_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    for item in validated_data:
        logger.info(f"[save_products] product_id={item.get('product_id')}, "
            f"category_id={item.get('category_id')}, category_name={item.get('category_name')}")
        
        category_obj = None
        if "category_id" in item and "category_name" in item:
            category_obj, _ = Category.objects.get_or_create(
                category_id=item["category_id"],
                defaults={"category_name": item["category_name"]}
            )
        else:
            logger.warning(f"[save_products] Product {item.get('product_id')} has no category!")

        product_obj, _ = Product.objects.get_or_create(
            product_id=item.get("product_id"),
            defaults={
                "product_name": item.get("product_name"),
                "category": category_obj,
                "cost": item.get("cost", 0),
                "fiscal": item.get("fiscal", True),
                "workshop": item.get("workshop", 0)
            }
        )

        # Обновляем существующий продукт
        product_obj.product_name = item["product_name"]
        product_obj.cost = item.get("cost", 0)
        product_obj.fiscal = item.get("fiscal", True)
        product_obj.workshop = item.get("workshop", 0)
        product_obj.save()



def save_products_sales(products_data: list[dict]):
    """
    Сохраняет продажи продуктов через сериализатор.
    """
    serializer = ProductSalesAPISerializer(data=products_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    for item in validated_data:
        logger.info(f"[save_products_sales] product_id={item.get('product_id')}, "
                    f"category_id={item.get('category_id')}, category_name={item.get('category_name')}")
        category_obj = None
        if "category_id" in item and "category_name" in item:
            category_obj, _ = Category.objects.get_or_create(
                category_id=item["category_id"],
                defaults={"name": item["category_name"]}
            )
        else:
            logger.warning(f"[save_products_sales] Product {item.get('product_id')} has no category!")

        product_obj, _ = Product.objects.get_or_create(
            product_id=item.get("product_id"),
            defaults={
                "product_name": item.get("name"),
                "category": category_obj,
                "cost": item.get("price", 0),
                "fiscal": True,
                "workshop": 0
            }
        )

        # Сохраняем или обновляем продажи
        sales_obj, _ = ProductSales.objects.get_or_create(
            product=product_obj,
            defaults={
                "product_profit": item.get("product_profit", 0),
                "count": int(item.get("count", 0))
            }
        )
        sales_obj.product_profit = item.get("product_profit", 0)
        sales_obj.count = int(item.get("count", 0))
        sales_obj.save()


def save_categories(categories_data: list[dict]):
    """
    Сохраняет категории через сериализатор.
    """
    serializer = CategoryAPISerializer(data=categories_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    for item in validated_data:
        category_obj, created = Category.objects.get_or_create(
            category_id=item["category_id"],
            defaults={"category_name": item["category_name"]}
        )

        if not created and category_obj.category_name != item["category_name"]:
            category_obj.category_name = item["category_name"]
            category_obj.save()



def save_categories_sales(categories_data: list[dict]):
    """
    Сохраняет продажи категорий через сериализатор.
    """
    serializer = CategoriesSalesAPISerializer(data=categories_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    for item in validated_data:
        category_obj, _ = Category.objects.get_or_create(
            category_id=item["category_id"],
            defaults={"category_name": item["category_name"]}
        )

        sales_obj, _ = CategoriesSales.objects.get_or_create(
            category=category_obj,
            defaults={
                "profit": item.get("profit", 0),
                "count": int(item.get("count", 0))
            }
        )
        sales_obj.profit = item.get("profit", 0)
        sales_obj.count = int(item.get("count", 0))
        sales_obj.save()



def parse_poster_datetime(value):
    """
    Парсит время из постера.
    value может быть:
    - timestamp в миллисекундах
    - строка формата 'YYYY-MM-DD HH:MM:SS'
    """
    if value is None:
        return None
    try:
        ts = int(value)
        if ts > 1e12:  
            ts = ts / 1000
        return datetime.fromtimestamp(ts)
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except Exception:
            logger.warning(f"Can't parse datetime: {value}")
            return None


# ------------------ Сохранение транзакций ------------------
def save_transactions(data: list[dict]) -> int:
    saved_count = 0

    for item in data:
        client_info = item.get("client", {})

        date_start = parse_poster_datetime(item.get("date_start"))
        date_close = parse_poster_datetime(item.get("date_close"))

        if timezone.is_naive(date_start):
            date_start = timezone.make_aware(date_start)
        if date_close and timezone.is_naive(date_close):
            date_close = timezone.make_aware(date_close)

        obj, created = Transactions.objects.get_or_create(
            transaction_id=item.get("transaction_id") or item.get("id"),
            defaults={
                "date_start": date_start,
                "date_close": date_close,
                "status": item.get("status"),
                "pay_type": item.get("pay_type"),
                "payed_sum": Decimal(item.get("payed_sum") or 0),
                "sum": Decimal(item.get("sum") or 0),
                "spot_id": item.get("spot_id"),
                "transaction_comment": item.get("comment"),
                "reason": item.get("reason"),
                "total_profit": Decimal(item.get("total_profit") or 0),
                "client_firstname": client_info.get("firstname", ""),
                "client_lastname": client_info.get("lastname", ""),
                "client_phone": client_info.get("phone", ""),
                "client_id": client_info.get("id"),
                "service_mode": item.get("service_mode"),
                "processing_status": item.get("processing_status"),
            }
        )
        if created:
            saved_count += 1

    return saved_count

# ------------------ Сохранение истории ------------------
def save_transaction_history(transaction_id: int, history_data: list[dict]) -> int:
    saved_count = 0
    try:
        transaction = Transactions.objects.get(transaction_id=transaction_id)
    except Transactions.DoesNotExist:
        logger.warning(f"Transaction {transaction_id} not found for history")
        return saved_count

    for h in history_data:
        history_time = parse_poster_datetime(h.get("time"))
        if timezone.is_naive(history_time):
            history_time = timezone.make_aware(history_time)

        try:
            value_text = json.loads(h.get("value_text") or "{}")
        except Exception:
            value_text = {}

        history_obj, created = TransactionHistory.objects.get_or_create(
            transaction=transaction,
            type_history=h.get("type_history"),
            time=history_time,
            defaults={
                "value": float(h.get("value", 0)),
                "value2": float(h.get("value2") or 0),
                "value3": float(h.get("value3") or 0),
                "value_text": value_text,
                "spot_tablet_id": h.get("spot_tablet_id"),
            }
        )
        if created:
            saved_count += 1
    return saved_count

# ------------------ Сохранение продуктов ------------------
def save_transactions_products(products_data: list[dict]):
    logger.info(f"[save_transactions_products] products_data sample: {products_data[:5]}")
    for item in products_data:
        logger.info(f"[save_transactions_products] product_id={item.get('product_id')}, "
                    f"category_id={item.get('category_id')}, category_name={item.get('category_name')}")

        
            
        try:
            tx_obj = Transactions.objects.get(transaction_id=item.get("transaction_id"))
        except Transactions.DoesNotExist:
            logger.warning(f"Transaction {item.get('transaction_id')} not found for products")
            continue

        client_obj = None
        client_data = item.get("client")
        if client_data:
            client_obj, _ = Clients.objects.get_or_create(
                client_id=client_data.get("id"),
                defaults={
                    "firstname": client_data.get("firstname", ""),
                    "lastname": client_data.get("lastname", ""),
                    "name": client_data.get("name"),
                    "phone": client_data.get("phone"),
                    "email": client_data.get("email", None),
                }
            )
            
        category_obj = None
        category_id = item.get("category_id")
        if category_id is not None:
            category_name = item.get("category_name") or f"Category {category_id}"
            category_obj, _ = Category.objects.get_or_create(
                category_id=category_id,
                defaults={"category_name": category_name}
            )
        else:
            logger.warning(f"Product {item.get('product_id')} has no category_id!")

        product_obj, _ = Product.objects.get_or_create(
            product_id=item.get("product_id"),
            defaults={
                "product_name": item.get("product_name"),
                "category": category_obj,
                "cost": float(item.get("product_cost", 0)),
                "workshop": int(item.get("workshop", 0))
            }
        )

        TransactionsProducts.objects.update_or_create(
            transaction=tx_obj,
            product=product_obj,
            client=client_obj,
            defaults={
                "num": float(item.get("num", 0)),
                "workshop": item.get("workshop", 0),
                "payed_sum": float(item.get("payed_sum", 0)),
                "product_cost": float(item.get("product_cost", 0)),
                "product_profit": float(item.get("product_profit", 0)),
            }
        )

# ------------------ Очистка старых транзакций ------------------
def delete_old_transactions():
    one_month_ago = timezone.now() - timedelta(days=30)
    old_tx_ids = Transactions.objects.filter(date_close__lt=one_month_ago).values_list('id', flat=True)

    TransactionsProducts.objects.filter(transaction_id__in=old_tx_ids).delete()
    TransactionHistory.objects.filter(transaction_id__in=old_tx_ids).delete()
    Transactions.objects.filter(date_close__lt=one_month_ago).delete()
    
    
        
def save_workshops(workshops_data: list[dict]):
    """
    Сохраняет список мастерских в таблицу Workshop через сериализатор.
    """
    serializer = WorkshopSerializer(data=workshops_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    for item in validated_data:
        workshop_obj, created = Workshop.objects.get_or_create(
            workshop_id=item["workshop_id"],
            defaults={
                "workshop_name": item["workshop_name"],
                "delete": item.get("delete", False)
            }
        )
        if not created:
            workshop_obj.workshop_name = item["workshop_name"]
            workshop_obj.delete = item.get("delete", False)
            workshop_obj.save()


def save_payment_methods(payments_data: list[dict]):
    """
    Сохраняет список методов оплаты в таблицу Payments_ID через сериализатор.
    """
    serializer = PaymentMethodSerializer(data=payments_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    for item in validated_data:
        payment_obj, created = Payments_ID.objects.get_or_create(
            payment_method_id=item["payment_method_id"],
            defaults={"title": item["title"]}
        )
        if not created:
            payment_obj.title = item["title"]
            payment_obj.save()



def save_clients(clients_data: list[dict]) -> int:
    """
    Сохраняет или обновляет клиентов из API-данных.

    Args:
        clients_data (list[dict]): список клиентов из Poster API

    Returns:
        int: количество новых записей
    """
    saved_count = 0

    for item in clients_data:
        client_obj, created = Clients.objects.update_or_create(
            client_id=item["client_id"],  
            defaults={
                "firstname": item.get("firstname", ""),
                "lastname": item.get("lastname", ""),
                "name": item.get("name"),
                "phone": item.get("phone", ""),
                "email": item.get("email", None),
                "revenue": item.get("revenue", 0),
                "profit": item.get("profit", 0),
                "transactions": item.get("transactions", 0),
            },
        )

        if created:
            saved_count += 1

    return saved_count







def sync_poster_day(api_client, date_str: str, spot_id: int = None):
    # 1. Получаем транзакции
    transactions_data = api_client.get_transactions(date_from=date_str, date_to=date_str, spot_id=spot_id)
    if not transactions_data:
        logger.warning(f"No transactions found for {date_str}")
        return

    save_transactions(transactions_data)
    transaction_ids = [tx["transaction_id"] for tx in transactions_data if "transaction_id" in tx]

    if transaction_ids:
        histories = []
        for tx_id in transaction_ids:
            response = api_client.make_request(
                "GET",
                "dash.getTransactionHistory",
                params={"transaction_id": tx_id}
            ).get("response", [])
            histories.append((tx_id, response, None, None))  

        for tx_id, history_actions, _, _ in histories:
            save_transaction_history(int(tx_id), history_actions)

        
        products_data = api_client.get_transactions_products(transaction_ids)
        save_transactions_products(products_data)

    logger.info(f"Sync finished for {date_str}, transactions: {len(transaction_ids)}")


# ------------------ Синхронный sync_poster_from_august ------------------
def sync_poster_from_august(api_client, spot_id: int = None):
    start_date = datetime(2025, 8, 1)
    end_date = datetime.now()
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        try:
            logger.info(f"Syncing Poster data for {date_str}")
            sync_poster_day(api_client, date_str, spot_id)
        except Exception as e:
            logger.error(f"Failed to sync {date_str}: {e}")
        current_date += timedelta(days=1)

    logger.info("All Poster data synced from August 2025 to today.")
    
    
    
    
def sync_all_from_date(api_client, start_date: str, spot_id: int = None):
    """
    Синхронизирует все данные из Poster API с указанной даты до сегодняшнего дня.
    Всегда обновляет существующие записи или создает новые.
    """
    start_dt = datetime.strptime(str(start_date), "%Y-%m-%d").date()
    end_dt = date.today()
    current_date = start_dt

    while current_date <= end_dt:
        date_str = current_date.strftime("%Y-%m-%d")
        logger.info(f"Syncing all Poster data for {date_str}")

        try:
            # Кассовые смены
            save_cash_shifts_range(api_client, date_str, spot_id)

            # Продажи по сменам
            save_shift_sales_to_db(api_client, date_str, spot_id)

            # Транзакции
            transactions_data = api_client.get_transactions(date_from=date_str, date_to=date_str, spot_id=spot_id)
            if transactions_data:
                save_transactions(transactions_data)
                transaction_ids = [tx["transaction_id"] for tx in transactions_data if "transaction_id" in tx]

                # История транзакций
                for tx_id in transaction_ids:
                    history = api_client.make_request(
                        "GET",
                        "dash.getTransactionHistory",
                        params={"transaction_id": tx_id}
                    ).get("response", [])
                    save_transaction_history(tx_id, history)

                # Продукты транзакций
                products_data = api_client.get_transactions_products(transaction_ids)
                save_transactions_products(products_data)

            # Продукты
            if hasattr(api_client, "get_products"):
                products_data = api_client.get_products()
                if products_data:
                    save_products(products_data)
                    save_products_sales(products_data)

            # Категории
            if hasattr(api_client, "get_categories"):
                categories_data = api_client.get_categories()
                if categories_data:
                    save_categories(categories_data)
                    save_categories_sales(categories_data)

            # Клиенты
            if hasattr(api_client, "get_clients"):
                clients_data = api_client.get_clients(date_from=date_str, date_to=date_str)
                if clients_data:
                    save_clients(clients_data)

            # Цех
            if hasattr(api_client, "get_workshops"):
                workshops_data = api_client.get_workshops()
                if workshops_data:
                    save_workshops(workshops_data)

            # Методы оплаты
            if hasattr(api_client, "get_payment_methods"):
                payments_data = api_client.get_payment_methods()
                if payments_data:
                    save_payment_methods(payments_data)

        except Exception as e:
            import traceback
            logger.error(f"Failed to sync {date_str}: {e}, type={type(e)}")
            traceback.print_exc()

        current_date += timedelta(days=1)

    logger.info(f"All Poster data synced from {start_date} to today.")
