from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
# from django.utils import timezone
from django.db import transaction


import json
import logging

from poster_api.client import PosterAPIClient
from users.models import Role
from ..decorators import timing_decorator


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



api_client = PosterAPIClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@timing_decorator
def save_shift_sales_to_db(api_client, date_str: str, spot_id: int = None):
    """
    Saves sales by shift in bulk.

    This function fetches sales data, then processes it in memory to prepare
    all parent (ShiftSale) and child (ShiftSaleItem) records.

    Args:
        api_client: An instance of the API client.
        date_str: The date for which to save sales ("YYYY-MM-DD").
        spot_id: The optional ID of the establishment.
    """
    try:
        sales_by_shift = api_client.get_sales_by_shift_with_delivery(date_str, spot_id)
    except Exception as e:
        logger.error(f"Failed to fetch sales data from API for date {date_str}: {e}")
        return

    if not sales_by_shift:
        logger.info(f"No sales data found for date {date_str}.")
        return

    try:
        api_shift_id_strs = list(sales_by_shift.keys())
        api_shift_ids = [int(sid) for sid in api_shift_id_strs]
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid shift_id key from API. Not all keys are integers: {e}. Keys: {sales_by_shift.keys()}")
        return

    shifts_data_prepared = {}
    for shift_id_str in api_shift_id_strs:
        try:
            shift_id = int(shift_id_str)
            shift_data = sales_by_shift[shift_id_str]
        except (ValueError, TypeError):
            logger.warning(f"Skipping non-integer shift_id {shift_id_str}.")
            continue
        except KeyError:
            continue
            
        try:
            reg_revenue = sum(Decimal(item.get('payed_sum', 0)) for item in shift_data.get('regular', []))
            del_revenue = sum(Decimal(item.get('payed_sum', 0)) for item in shift_data.get('delivery', []))
            reg_profit = sum(Decimal(item.get('profit', 0)) for item in shift_data.get('regular', []))
            del_profit = sum(Decimal(item.get('profit', 0)) for item in shift_data.get('delivery', []))
            
            total_revenue = reg_revenue + del_revenue
            total_profit = reg_profit + del_profit
            
            percentage = (total_profit / total_revenue * 100) if total_revenue else Decimal(0)

            shifts_data_prepared[shift_id] = {
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_percentage': percentage,
                'total_delivery_revenue': del_revenue,
                'total_delivery_profit': del_profit,
                'tips': Decimal(shift_data.get('tips', '0.0')),
            }
        except (InvalidOperation, TypeError) as e:
            logger.warning(f"Skipping shift {shift_id} due to invalid decimal data: {e}")
            continue
            
    with transaction.atomic():
        existing_shifts = {
            s.shift_id: s for s in ShiftSale.objects.filter(shift_id__in=api_shift_ids, date=date_str)
        }
        shifts_to_create = []
        shifts_to_update = []
        
        for shift_id, defaults in shifts_data_prepared.items():
            if shift_id in existing_shifts:
                shift_obj = existing_shifts[shift_id]
                has_changed = False
                for key, value in defaults.items():
                    if getattr(shift_obj, key) != value:
                        setattr(shift_obj, key, value)
                        has_changed = True
                if has_changed:
                    shifts_to_update.append(shift_obj)
            else:
                shifts_to_create.append(ShiftSale(shift_id=shift_id, date=date_str, **defaults))
        
        if shifts_to_create:
            ShiftSale.objects.bulk_create(shifts_to_create)
        if shifts_to_update:
            if shifts_data_prepared:
                update_fields = shifts_data_prepared[list(shifts_data_prepared.keys())[0]].keys()
                ShiftSale.objects.bulk_update(shifts_to_update, update_fields)


        shift_obj_map = {
            s.shift_id: s for s in ShiftSale.objects.filter(shift_id__in=api_shift_ids, date=date_str)
        }

        existing_items = ShiftSaleItem.objects.filter(shift_sale__in=shift_obj_map.values())
        
        existing_items_map = {
            (item.shift_sale.shift_id, item.product_name or "", item.category_name): item for item in existing_items
        }

        items_to_create = []
        items_to_update = []
        
        for shift_id_str in api_shift_id_strs:
            try:
                shift_id = int(shift_id_str)
                shift_data = sales_by_shift[shift_id_str]
            except (ValueError, TypeError, KeyError):
                continue 

            shift_obj = shift_obj_map.get(shift_id) 
            if not shift_obj:
                logger.warning(f"ShiftSale object for shift_id {shift_id} not found in DB map. Skipping items.")
                continue

            for category in ['regular', 'delivery']:
                for product in shift_data.get(category, []):
                    try:
                        defaults = {
                            'count': product.get('count', 0),
                            'product_sum': Decimal(product.get('product_sum', '0.0')),
                            'payed_sum': Decimal(product.get('payed_sum', '0.0')),
                            'profit': Decimal(product.get('profit', '0.0')),
                            'workshop': product.get('workshop'),
                            'delivery_service': product.get('delivery_service') if category == 'delivery' else None,
                            'tips': Decimal(product.get('tips', '0.0')),
                        }
                    except (InvalidOperation, TypeError):
                        logger.warning(f"Skipping product {product.get('product_name')} in shift {shift_id} due to invalid data.")
                        continue
                    
                    product_name = product.get('product_name') or ""
                    
                    item_key = (shift_id, product_name, category)
                    
                    if item_key in existing_items_map:
                        item_obj = existing_items_map[item_key]
                        has_changed_item = False
                        for key, value in defaults.items():
                            if getattr(item_obj, key) != value:
                                setattr(item_obj, key, value)
                                has_changed_item = True
                        if has_changed_item:
                            items_to_update.append(item_obj)
                    else:
                        items_to_create.append(
                            ShiftSaleItem(
                                shift_sale=shift_obj,
                                product_name=product_name,
                                category_name=category,
                                **defaults
                            )
                        )

        if items_to_create:
            ShiftSaleItem.objects.bulk_create(items_to_create)
        if items_to_update:
            item_update_fields = ['count', 'product_sum', 'payed_sum', 'profit', 'workshop', 'delivery_service', 'tips']
            ShiftSaleItem.objects.bulk_update(items_to_update, item_update_fields)
            
    logger.info(f"Processed sales for {date_str}. Shifts: {len(shifts_to_create)} created, {len(shifts_to_update)} updated. Items: {len(items_to_create)} created, {len(items_to_update)} updated.")


def _parse_and_make_aware(date_str: Optional[str]) -> Optional[datetime]:
    """Helper to parse a date string and return a timezone-aware UTC datetime."""
    if not date_str or date_str == '0000-00-00 00:00:00':
        return None
    try:
        naive_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return naive_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse datetime string: {date_str}")
        return None


@timing_decorator
def save_cash_shifts_range(api_client, start_date: str, spot_id: int = None, end_date: str = None):
    """
    Saves cash shifts from an API in bulk for a given date range.

    This function fetches all cash shifts for the entire specified date range
    in a single API call and then uses bulk database operations to create or
    update the records.

    Args:
        api_client: An instance of the Poster API client.
        start_date: The start date of the range (e.g., "2025-10-13").
        end_date: The optional end date. Defaults to start_date.
        spot_id: The optional ID of the establishment.
    """
    end_date = end_date or start_date

    try:
        all_shifts = api_client.get_cash_shifts(
            date_from=start_date, date_to=end_date, spot_id=spot_id
        )
    except Exception as e:
        logger.error(f"Failed to fetch cash shifts from API: {e}")
        return

    if not all_shifts:
        logger.info("No cash shifts found for the specified period.")
        return

    shift_ids = {shift['poster_shift_id'] for shift in all_shifts}

    with transaction.atomic():
        existing_shifts_map = {
            s.poster_shift_id: s for s in CashShiftReport.objects.filter(poster_shift_id__in=shift_ids)
        }

        shifts_to_create = []
        shifts_to_update = []
        fields_for_update = [
            'date_start', 'date_end', 'cash_start', 'cash_end', 'amount_debit',
            'amount_sell_cash', 'amount_sell_card', 'amount_credit',
            'amount_collection', 'total_sales', 'comment', 'user_id_start', 'user_id_end'
        ]

        for shift in all_shifts:
            try:
                sell_cash = Decimal(shift.get('amount_sell_cash', 0) or 0)
                sell_card = Decimal(shift.get('amount_sell_card', 0) or 0)
                total_sales = sell_cash + sell_card

                defaults = {
                    'date_start': _parse_and_make_aware(shift.get('date_start')),
                    'date_end': _parse_and_make_aware(shift.get('date_end')),
                    'cash_start': Decimal(shift.get('amount_start', 0) or 0),
                    'cash_end': Decimal(shift.get('amount_end', 0) or 0),
                    'amount_debit': Decimal(shift.get('amount_debit', 0) or 0),
                    'amount_sell_cash': sell_cash,
                    'amount_sell_card': sell_card,
                    'amount_credit': Decimal(shift.get('amount_credit', 0) or 0),
                    'amount_collection': Decimal(shift.get('amount_collection', 0) or 0),
                    'total_sales': total_sales,
                    'comment': shift.get('comment'),
                    'user_id_start': shift.get('user_id_start'),
                    'user_id_end': shift.get('user_id_end'),
                }
            except (InvalidOperation, TypeError) as e:
                logger.warning(f"Skipping shift {shift.get('poster_shift_id')} due to invalid decimal data: {e}")
                continue

            existing_shift = existing_shifts_map.get(shift['poster_shift_id'])
            if existing_shift:
                for field, value in defaults.items():
                    setattr(existing_shift, field, value)
                shifts_to_update.append(existing_shift)
            else:
                shifts_to_create.append(
                    CashShiftReport(poster_shift_id=shift['poster_shift_id'], **defaults)
                )

        if shifts_to_create:
            CashShiftReport.objects.bulk_create(shifts_to_create)
        if shifts_to_update:
            CashShiftReport.objects.bulk_update(shifts_to_update, fields_for_update)
            
        logger.info(f"Cash shifts saved. Created: {len(shifts_to_create)}, Updated: {len(shifts_to_update)}.")


@timing_decorator
def save_products(products_data: list[dict]):
    """
    Bulk creates or updates products and their associated categories from a list of data.

    Args:
        products_data (list[dict]): A list of dictionaries, where each dictionary
            represents a product and should contain keys like 'product_id',
            'product_name', 'category_id', 'category_name', 'cost', etc.

    Raises:
        rest_framework.exceptions.ValidationError: If the input data is not valid.
    """
    if not products_data:
        logger.info("[save_products] Received empty list of products. Nothing to do.")
        return

    serializer = ProductAPISerializer(data=products_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    with transaction.atomic():
        categories_to_process = {
            item['category_id']: {'category_name': item['category_name']}
            for item in validated_data if 'category_id' in item and 'category_name' in item
        }
        
        if categories_to_process:
            category_instances = [
                Category(category_id=cat_id, category_name=data['category_name'])
                for cat_id, data in categories_to_process.items()
            ]
            Category.objects.bulk_create(category_instances, ignore_conflicts=True)

        category_ids = categories_to_process.keys()
        category_map = {cat.category_id: cat for cat in Category.objects.filter(category_id__in=category_ids)}

        product_ids = [item['product_id'] for item in validated_data]
        existing_products_map = {p.product_id: p for p in Product.objects.filter(product_id__in=product_ids)}

        products_to_create = []
        products_to_update = []
        
        for item in validated_data:
            product_id = item['product_id']
            category_id = item.get('category_id')
            category_obj = category_map.get(category_id)

            if not category_obj:
                logger.warning(f"[save_products] Product {product_id} has a missing or invalid category_id: {category_id}. Skipping.")
                continue

            if product_id in existing_products_map:
                product_obj = existing_products_map[product_id]
                product_obj.product_name = item["product_name"]
                product_obj.category = category_obj
                product_obj.cost = item.get("cost", 0)
                product_obj.fiscal = item.get("fiscal", True)
                product_obj.workshop = item.get("workshop", 0)
                products_to_update.append(product_obj)
            else:
                products_to_create.append(
                    Product(
                        product_id=product_id,
                        product_name=item["product_name"],
                        category=category_obj,
                        cost=item.get("cost", 0),
                        fiscal=item.get("fiscal", True),
                        workshop=item.get("workshop", 0)
                    )
                )

        if products_to_create:
            Product.objects.bulk_create(products_to_create)
            logger.info(f"[save_products] Created {len(products_to_create)} new products.")

        if products_to_update:
            fields_to_update = ["product_name", "category", "cost", "fiscal", "workshop"]
            Product.objects.bulk_update(products_to_update, fields_to_update)
            logger.info(f"[save_products] Updated {len(products_to_update)} existing products.")



@timing_decorator
def save_products_sales(products_data: list[dict]):
    """
    Bulk creates or updates product sales records from a list of data.

    Args:
        products_data (list[dict]): A list of dictionaries, where each dictionary
            represents a product sale. Expected keys include 'product_id', 'name',
            'category_id', 'category_name', 'price', 'count', and 'product_profit'.

    Raises:
        rest_framework.exceptions.ValidationError: If the input data fails validation.
    """
    if not products_data:
        logger.info("[save_products_sales] Received empty list. Nothing to process.")
        return
    
    valid_data = [
        item for item in products_data 
        if item.get('product_name') and item.get('category_name')
    ]
    
    if len(valid_data) < len(products_data):
        logger.warning(f"[save_products_sales] Filtered out {len(products_data) - len(valid_data)} items with missing name or category.")

    if not valid_data:
        logger.info("[save_products_sales] No valid data left after filtering.")
        return
    
    
    serializer = ProductSalesAPISerializer(data=valid_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    with transaction.atomic():
        categories_to_process = {
            item['category_id']: {'name': item['category_name']}
            for item in validated_data if 'category_id' in item and 'category_name' in item
        }
        if categories_to_process:
            category_instances = [
                Category(category_id=cat_id, name=data['name'])
                for cat_id, data in categories_to_process.items()
            ]
            Category.objects.bulk_create(category_instances, ignore_conflicts=True)
        
        category_map = {c.category_id: c for c in Category.objects.filter(category_id__in=categories_to_process.keys())}

        product_ids = {item['product_id'] for item in validated_data}
        existing_products = {p.product_id: p for p in Product.objects.filter(product_id__in=product_ids)}
        
        products_to_create = []
        for item in validated_data:
            if item['product_id'] not in existing_products:
                category_obj = category_map.get(item.get('category_id'))
                products_to_create.append(
                    Product(
                        product_id=item['product_id'],
                        product_name=item.get("name"),
                        category=category_obj,
                        cost=item.get("price", 0),
                        fiscal=True,
                        workshop=0
                    )
                )
        
        if products_to_create:
            Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
            logger.info(f"[save_products_sales] Created {len(products_to_create)} new products.")

        product_map = {p.product_id: p for p in Product.objects.filter(product_id__in=product_ids)}
        
        existing_sales = {s.product_id: s for s in ProductSales.objects.filter(product_id__in=product_ids)}
        
        sales_to_create = []
        sales_to_update = []
        
        for item in validated_data:
            product_obj = product_map.get(item['product_id'])
            if not product_obj:
                logger.warning(f"[save_products_sales] Could not find or create product with id {item['product_id']}. Skipping sale.")
                continue

            if product_obj.product_id in existing_sales:
                sale_obj = existing_sales[product_obj.product_id]
                sale_obj.product_profit = item.get("product_profit", 0)
                sale_obj.count = int(item.get("count", 0))
                sales_to_update.append(sale_obj)
            else:
                sales_to_create.append(
                    ProductSales(
                        product=product_obj,
                        product_profit=item.get("product_profit", 0),
                        count=int(item.get("count", 0))
                    )
                )

        if sales_to_create:
            ProductSales.objects.bulk_create(sales_to_create)
            logger.info(f"[save_products_sales] Created {len(sales_to_create)} new sales records.")

        if sales_to_update:
            ProductSales.objects.bulk_update(sales_to_update, ["product_profit", "count"])
            logger.info(f"[save_products_sales] Updated {len(sales_to_update)} existing sales records.")


@timing_decorator
def save_categories(categories_data: list[dict]):
    """
    Bulk creates new categories or updates existing ones from a list of data.

    Args:
        categories_data (list[dict]): A list of dictionaries, where each should
            contain 'category_id' and 'category_name'.

    Raises:
        rest_framework.exceptions.ValidationError: If the input data is invalid.
    """
    if not categories_data:
        logger.info("[save_categories] Received empty list of categories. Nothing to do.")
        return
    
    valid_data = [
        item for item in categories_data
        if item.get('category_name') 
    ]
    
    if len(valid_data) < len(categories_data):
        logger.warning(f"[save_categories_sales] Filtered out {len(categories_data) - len(valid_data)} items with missing category name.")

    if not valid_data:
        logger.info("[save_categories_sales] No valid data left after filtering.")
        return

    serializer = CategoryAPISerializer(data=valid_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    with transaction.atomic():
        category_ids = {item['category_id'] for item in validated_data}
        
        existing_categories_map = {
            c.category_id: c for c in Category.objects.filter(category_id__in=category_ids)
        }

        categories_to_create = []
        categories_to_update = []

        for item in validated_data:
            category_id = item['category_id']
            category_name = item['category_name']
            
            existing_category = existing_categories_map.get(category_id)

            if existing_category is None:
                categories_to_create.append(
                    Category(category_id=category_id, category_name=category_name)
                )
            elif existing_category.category_name != category_name:
                existing_category.category_name = category_name
                categories_to_update.append(existing_category)
        
        if categories_to_create:
            Category.objects.bulk_create(categories_to_create)
            logger.info(f"[save_categories] Created {len(categories_to_create)} new categories.")
        
        if categories_to_update:
            Category.objects.bulk_update(categories_to_update, ['category_name'])
            logger.info(f"[save_categories] Updated {len(categories_to_update)} existing categories.")


@timing_decorator
def save_categories_sales(categories_data: list[dict]):
    """
    Bulk creates or updates category sales records from a list of data.

    Args:
        categories_data (list[dict]): A list of dictionaries, where each
            represents a category sale. Expected keys include 'category_id',
            'category_name', 'profit', and 'count'.

    Raises:
        rest_framework.exceptions.ValidationError: If the input data fails validation.
    """
    if not categories_data:
        logger.info("[save_categories_sales] Received empty list. Nothing to process.")
        return

    
    valid_data = [
        item for item in categories_data
        if item.get('category_name') 
    ]
    
    if len(valid_data) < len(categories_data):
        logger.warning(f"[save_categories_sales] Filtered out {len(categories_data) - len(valid_data)} items with missing category name.")

    if not valid_data:
        logger.info("[save_categories_sales] No valid data left after filtering.")
        return
    
    
    serializer = CategoriesSalesAPISerializer(data=valid_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    with transaction.atomic():
        categories_to_ensure = {
            item['category_id']: {'category_name': item['category_name']}
            for item in validated_data
        }
        category_instances = [
            Category(category_id=cat_id, category_name=data['category_name'])
            for cat_id, data in categories_to_ensure.items()
        ]
        Category.objects.bulk_create(category_instances, ignore_conflicts=True)

        category_map = {
            c.category_id: c for c in Category.objects.filter(category_id__in=categories_to_ensure.keys())
        }

        existing_sales_map = {
            s.category_id: s for s in CategoriesSales.objects.filter(category_id__in=category_map.keys())
        }

        sales_to_create = []
        sales_to_update = []

        for item in validated_data:
            category_id = item['category_id']
            category_obj = category_map.get(category_id)
            if not category_obj:
                logger.warning(f"[save_categories_sales] Category object for id {category_id} not found. Skipping.")
                continue

            if category_id in existing_sales_map:
                sale_obj = existing_sales_map[category_id]
                sale_obj.profit = item.get("profit", 0)
                sale_obj.count = int(item.get("count", 0))
                sales_to_update.append(sale_obj)
            else:
                sales_to_create.append(
                    CategoriesSales(
                        category=category_obj,
                        profit=item.get("profit", 0),
                        count=int(item.get("count", 0))
                    )
                )

        if sales_to_create:
            CategoriesSales.objects.bulk_create(sales_to_create)
            logger.info(f"[save_categories_sales] Created {len(sales_to_create)} new sales records.")

        if sales_to_update:
            CategoriesSales.objects.bulk_update(sales_to_update, ["profit", "count"])
            logger.info(f"[save_categories_sales] Updated {len(sales_to_update)} existing sales records.")

def parse_poster_datetime(value: Any) -> Optional[datetime]:
    """
    Parses a datetime from various Poster API formats into a timezone-aware datetime object.

    The function handles:
    - An integer or float timestamp (in seconds or milliseconds).
    - A string in 'YYYY-MM-DD HH:MM:SS' format, assumed to be UTC.
    - None values.

    All successful parses result in a timezone-aware datetime object in UTC.

    Args:
        value (Any): The input value to parse.

    Returns:
        Optional[datetime]: A timezone-aware datetime object (in UTC) if parsing is
                            successful, otherwise None.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            if value > 1e12: 
                value /= 1000
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Could not parse timestamp '{value}': {e}")
            return None

    if isinstance(value, str):
        try:
            num_value = float(value)
            if num_value > 1e12: 
                num_value /= 1000
            return datetime.fromtimestamp(num_value, tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            pass
        try:
            naive_dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return naive_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse datetime string '{value}' (as string or timestamp): {e}")
            return None

    logger.warning(f"Unsupported type for datetime parsing: {type(value)}")
    return None



@timing_decorator
def save_transactions(data: List[Dict]) -> int:
    """
    Bulk saves new transaction records from a list of data.

    Args:
        data: A list of dictionaries, where each dictionary represents a transaction.

    Returns:
        The number of newly saved transaction records.
    """
    if not data:
        return 0

    incoming_ids = {item.get("transaction_id") or item.get("id") for item in data}
    incoming_ids.discard(None)

    existing_ids = set(
        Transactions.objects.filter(transaction_id__in=incoming_ids)
        .values_list('transaction_id', flat=True)
    )

    transactions_to_create = []
    for item in data:
        transaction_id = item.get("transaction_id") or item.get("id")
        if not transaction_id or transaction_id in existing_ids:
            continue

        client_info = item.get("client", {})

        date_start = parse_poster_datetime(item.get("date_start"))
        date_close = parse_poster_datetime(item.get("date_close"))

        transactions_to_create.append(
            Transactions(
                transaction_id=transaction_id,
                date_start=date_start,
                date_close=date_close,
                status=item.get("status"),
                pay_type=item.get("pay_type"),
                payed_sum=Decimal(item.get("payed_sum") or 0),
                sum=Decimal(item.get("sum") or 0),
                spot_id=item.get("spot_id"),
                transaction_comment=item.get("comment"),
                reason=item.get("reason"),
                total_profit=Decimal(item.get("total_profit") or 0),
                client_firstname=client_info.get("firstname", ""),
                client_lastname=client_info.get("lastname", ""),
                client_phone=client_info.get("phone", ""),
                client_id=client_info.get("id"),
                service_mode=item.get("service_mode"),
                processing_status=item.get("processing_status"),
            )
        )
        existing_ids.add(transaction_id)


    if transactions_to_create:
        with transaction.atomic():
            Transactions.objects.bulk_create(transactions_to_create, ignore_conflicts=True)

    return len(transactions_to_create)



@timing_decorator
def save_transaction_history(transaction_id: int, history_data: List[Dict]) -> int:
    """
    Bulk saves new history records for a specific transaction.

    Args:
        transaction_id: The ID of the parent transaction.
        history_data: A list of dictionaries, each representing a history event.

    Returns:
        The number of newly saved history records.
    """
    if not history_data:
        return 0

    try:
        tx_obj = Transactions.objects.get(transaction_id=transaction_id)
    except Transactions.DoesNotExist:
        logger.warning(f"Transaction {transaction_id} not found for history save")
        return 0

    existing_history = TransactionHistory.objects.filter(transaction=tx_obj)
    
    existing_keys = {(h.type_history, h.time) for h in existing_history}

    history_to_create = []
    for h in history_data:
        history_time = parse_poster_datetime(h.get("time"))
        if not history_time:
            continue  

        current_key = (h.get("type_history"), history_time)
        if current_key in existing_keys:
            continue

        try:
            value_text = json.loads(h.get("value_text") or "{}")
        except (json.JSONDecodeError, TypeError):
            value_text = {}

        history_to_create.append(
            TransactionHistory(
                transaction=tx_obj,
                type_history=h.get("type_history"),
                time=history_time,
                value=float(h.get("value", 0)),
                value2=float(h.get("value2") or 0),
                value3=float(h.get("value3") or 0),
                value_text=value_text,
                spot_tablet_id=h.get("spot_tablet_id"),
            )
        )
        existing_keys.add(current_key)

    if history_to_create:
        with transaction.atomic():
            TransactionHistory.objects.bulk_create(history_to_create)

    return len(history_to_create)


@timing_decorator
def save_transactions_products(products_data: List[Dict]):
    """
    Bulk saves or updates product-transaction link records from a list of data.

    1. Collects all unique IDs for related models (Transactions, Clients, etc.).
    2. Fetches all existing objects and creates missing ones in bulk.
    3. Separates the main TransactionsProducts records into 'create' and 'update' lists and executes them in bulk.

    Args:
        products_data: A list of dictionaries, where each represents a product within a transaction.
    """
    if not products_data:
        logger.info("[save_transactions_products] Received empty list.")
        return

    tx_ids: Set[int] = set()
    client_ids: Set[int] = set()
    category_ids: Set[int] = set()
    product_ids: Set[int] = set()
    clients_to_create_data: Dict[int, Dict[str, Any]] = {}

    for item in products_data:
        tx_ids.add(item.get("transaction_id"))
        product_ids.add(item.get("product_id"))
        if cat_id := item.get("category_id"):
            category_ids.add(cat_id)
        if client_data := item.get("client"):
            if client_id := client_data.get("id"):
                client_ids.add(client_id)
                if client_id not in clients_to_create_data:
                    clients_to_create_data[client_id] = client_data


    with transaction.atomic():
        tx_map = {tx.transaction_id: tx for tx in Transactions.objects.filter(transaction_id__in=tx_ids)}
        client_map = {c.client_id: c for c in Clients.objects.filter(client_id__in=client_ids)}
        category_map = {c.category_id: c for c in Category.objects.filter(category_id__in=category_ids)}
        product_map = {p.product_id: p for p in Product.objects.filter(product_id__in=product_ids)}

        new_client_ids = client_ids - client_map.keys()
        new_clients = [
            Clients(
                client_id=cid,
                defaults={
                    "firstname": clients_to_create_data[cid].get("firstname", ""),
                    "lastname": clients_to_create_data[cid].get("lastname", ""),
                    "name": clients_to_create_data[cid].get("name"),
                    "phone": clients_to_create_data[cid].get("phone"),
                    "email": clients_to_create_data[cid].get("email"),
                }
            ) for cid in new_client_ids
        ]
        if new_clients:
            created_clients = Clients.objects.bulk_create(new_clients)
            for client in created_clients:
                client_map[client.client_id] = client 

        existing_links = TransactionsProducts.objects.filter(
            transaction__transaction_id__in=tx_ids,
            product__product_id__in=product_ids
        ).select_related('transaction', 'product', 'client')

        existing_links_map = {
            (link.transaction.transaction_id, link.product.product_id): link
            for link in existing_links
        }

        to_create = []
        to_update = []

        for item in products_data:
            tx_obj = tx_map.get(item.get("transaction_id"))
            product_obj = product_map.get(item.get("product_id"))
            
            client_obj = None
            if client_data := item.get("client"):
                client_obj = client_map.get(client_data.get("id"))

            if not tx_obj or not product_obj:
                logger.warning(f"Skipping record due to missing transaction or product. TX_ID: {item.get('transaction_id')}, Product_ID: {item.get('product_id')}")
                continue
            
            link_key = (tx_obj.transaction_id, product_obj.product_id)
            defaults = {
                "client": client_obj,
                "num": float(item.get("num", 0)),
                "workshop": item.get("workshop", 0),
                "payed_sum": float(item.get("payed_sum", 0)),
                "product_cost": float(item.get("product_cost", 0)),
                "product_profit": float(item.get("product_profit", 0)),
            }

            if link_key in existing_links_map:
                link_obj = existing_links_map[link_key]
                for key, value in defaults.items():
                    setattr(link_obj, key, value)
                to_update.append(link_obj)
            else:
                to_create.append(
                    TransactionsProducts(
                        transaction=tx_obj,
                        product=product_obj,
                        **defaults
                    )
                )

        if to_create:
            TransactionsProducts.objects.bulk_create(to_create)
        if to_update:
            fields_to_update = ["client", "num", "workshop", "payed_sum", "product_cost", "product_profit"]
            TransactionsProducts.objects.bulk_update(to_update, fields_to_update)

        logger.info(f"Processed transaction products. Created: {len(to_create)}, Updated: {len(to_update)}.")



@timing_decorator
def save_workshop(workshops_data: List[Dict]):
    """
    Bulk creates or updates workshop records from a list of data.

    Args:
        workshops_data: A list of dictionaries, where each should
                        contain 'workshop_id' and 'workshop_name'.
    """
    if not workshops_data:
        logger.info("[save_workshop] Received empty list. Nothing to process.")
        return

    serializer = WorkshopSerializer(data=workshops_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    workshop_ids = {item['workshop_id'] for item in validated_data}
    
    with transaction.atomic():
        existing_workshops_map = {
            w.workshop_id: w for w in Workshop.objects.filter(workshop_id__in=workshop_ids)
        }

        workshops_to_create = []
        workshops_to_update = []

        for item in validated_data:
            workshop_id = item["workshop_id"]
            existing_workshop = existing_workshops_map.get(workshop_id)

            if existing_workshop:
                new_name = item["workshop_name"]
                new_delete_flag = item.get("delete", False)

                if (existing_workshop.workshop_name != new_name or 
                    existing_workshop.delete != new_delete_flag):
                    existing_workshop.workshop_name = new_name
                    existing_workshop.delete = new_delete_flag
                    workshops_to_update.append(existing_workshop)
            else:
                workshops_to_create.append(
                    Workshop(
                        workshop_id=workshop_id,
                        workshop_name=item["workshop_name"],
                        delete=item.get("delete", False)
                    )
                )

        if workshops_to_create:
            Workshop.objects.bulk_create(workshops_to_create)
            logger.info(f"[save_workshop] Created {len(workshops_to_create)} new workshops.")

        if workshops_to_update:
            Workshop.objects.bulk_update(workshops_to_update, ["workshop_name", "delete"])
            logger.info(f"[save_workshop] Updated {len(workshops_to_update)} existing workshops.")



@timing_decorator
def save_payments_id(payments_data: List[Dict]):
    """
    Bulk creates or updates payment method records from a list of data.

    Args:
        payments_data: A list of dictionaries, where each should contain 'payment_method_id' and 'title'.
    """
    if not payments_data:
        logger.info("[save_payments_id] Received empty list. Nothing to process.")
        return

    serializer = PaymentMethodSerializer(data=payments_data, many=True)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    payment_ids = {item['payment_method_id'] for item in validated_data}

    with transaction.atomic():
        existing_payments_map = {
            p.payment_method_id: p for p in Payments_ID.objects.filter(payment_method_id__in=payment_ids)
        }

        to_create = []
        to_update = []

        for item in validated_data:
            payment_id = item["payment_method_id"]
            existing_payment = existing_payments_map.get(payment_id)

            if existing_payment:
                if existing_payment.title != item["title"]:
                    existing_payment.title = item["title"]
                    to_update.append(existing_payment)
            else:
                to_create.append(
                    Payments_ID(
                        payment_method_id=payment_id,
                        title=item["title"]
                    )
                )

        if to_create:
            Payments_ID.objects.bulk_create(to_create)
            logger.info(f"[save_payments_id] Created {len(to_create)} new payment methods.")

        if to_update:
            Payments_ID.objects.bulk_update(to_update, ["title"])
            logger.info(f"[save_payments_id] Updated {len(to_update)} existing payment methods.")
            




@timing_decorator
def save_clients(clients_data: List[Dict]) -> int:
    """
    Bulk creates or updates client records from a list of data.

    Args:
        clients_data: A list of dictionaries, each representing a client.

    Returns:
        The number of newly created client records.
    """
    if not clients_data:
        return 0

    clients_data_map = {item['client_id']: item for item in clients_data}
    client_ids = clients_data_map.keys()

    with transaction.atomic():
        existing_clients_map = {
            c.client_id: c for c in Clients.objects.filter(client_id__in=client_ids)
        }

        clients_to_create = []
        clients_to_update = []
        fields_for_update = [
            "firstname", "lastname", "name", "phone", "email",
            "revenue", "profit", "transactions"
        ]

        for client_id, item in clients_data_map.items():
            defaults = {
                "firstname": item.get("firstname", ""),
                "lastname": item.get("lastname", ""),
                "name": item.get("name"),
                "phone": item.get("phone", ""),
                "email": item.get("email"),
                "revenue": item.get("revenue", 0),
                "profit": item.get("profit", 0),
                "transactions": item.get("transactions", 0),
            }

            if client_id in existing_clients_map:
                client_obj = existing_clients_map[client_id]
                has_changed = False
                for field, value in defaults.items():
                    if getattr(client_obj, field) != value:
                        setattr(client_obj, field, value)
                        has_changed = True
                if has_changed:
                    clients_to_update.append(client_obj)
            else:
                clients_to_create.append(Clients(client_id=client_id, **defaults))

        if clients_to_create:
            Clients.objects.bulk_create(clients_to_create)
            logger.info(f"[save_clients] Created {len(clients_to_create)} new clients.")

        if clients_to_update:
            Clients.objects.bulk_update(clients_to_update, fields_for_update)
            logger.info(f"[save_clients] Updated {len(clients_to_update)} existing clients.")

    return len(clients_to_create)


@timing_decorator
def sync_all_from_date(api_client, start_date: str, spot_id: int = None):
    """
    Syncs all data from the Poster API for a given date range.
    """
    end_date = date.today().strftime("%Y-%m-%d")
    logger.info(f"Starting full data sync from {start_date} to {end_date}.")

    logger.info("--- Phase 1: Syncing static data ---")
    try:
        save_workshop(api_client.get_workshop())
        save_payments_id(api_client.get_payments_id())
        save_products(api_client.get_products())
        save_categories(api_client.get_category())
    except Exception as e:
        logger.error(f"FATAL: Could not sync static data. Aborting. Error: {e}", exc_info=True)
        return

    logger.info(f"--- Phase 2: Fetching range data from {start_date} to {end_date} ---")
    try:
        save_cash_shifts_range(api_client, start_date, spot_id, end_date)
        
        products_sales = api_client.get_products_sales(date_from=start_date, date_to=end_date, spot_id=spot_id)
        save_products_sales(products_sales)

        categories_sales = api_client.get_categories_sales(date_from=start_date, date_to=end_date, spot_id=spot_id)
        save_categories_sales(categories_sales)
        
        clients_sales = api_client.get_clients_sales(date_from=start_date, date_to=end_date, spot_id=spot_id)
        save_clients(clients_sales)
        
        all_transactions = api_client.get_transactions(date_from=start_date, date_to=end_date, spot_id=spot_id)
        save_transactions(all_transactions)

    except Exception as e:
        logger.error(f"ERROR: Failed during bulk data fetch for range {start_date}-{end_date}. Error: {e}", exc_info=True)
    
    logger.info("--- Phase 3: Handling nested dependencies ---")
    if all_transactions:
        transaction_ids = [tx.get("transaction_id") for tx in all_transactions if tx.get("transaction_id")]
        
        try:
            transactions_products = api_client.get_transactions_products(transaction_ids)
            save_transactions_products(transactions_products)
        except Exception as e:
            logger.error(f"ERROR: Failed to sync transaction products. Error: {e}", exc_info=True)
            
        
        logger.info(f"Fetching history for {len(transaction_ids)} transactions...")
        for i, tx_id in enumerate(transaction_ids):
            try:
                if (i + 1) % 100 == 0:
                    logger.info(f"  ...fetched history for {i + 1}/{len(transaction_ids)} transactions.")
                history = api_client.make_request(
                    "GET", "dash.getTransactionHistory", params={"transaction_id": tx_id}
                ).get("response", [])
                save_transaction_history(tx_id, history)
            except Exception as e:
                logger.error(f"ERROR: Failed to get history for transaction {tx_id}. Error: {e}")
                continue 

    logger.info("--- Phase 4: Syncing data from single-day-only endpoints ---")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = date.today()
    current_date = start_dt
    
    while current_date <= end_dt:
        date_str = current_date.strftime("%Y-%m-%d")
        logger.info(f"Syncing single-day data for {date_str}")
        try:
            save_shift_sales_to_db(api_client, date_str, spot_id)
        except Exception as e:
            logger.error(f"ERROR: Failed to sync shift sales for {date_str}. Error: {e}", exc_info=True)
        
        current_date += timedelta(days=1)

    logger.info(f"--- Sync Complete: All Poster data synced from {start_date} to {end_date}. ---")


def create_role_lists(api_client):
    """Creates predefined roles in the database efficiently."""
    roles_to_ensure = [
        'Официант', 'Бармен', 'Старший Бармен', 'Кальянный мастер',
        'Старший Кальянный мастер', 'Менеджер', 'Управляющий', 'Уборщик',
        'Повар', 'Шеф-Повар', 'SMM', 'Доставщик', 'Курьер',
    ]
    
    role_objects = [Role(name=role) for role in roles_to_ensure]
    Role.objects.bulk_create(role_objects, ignore_conflicts=True)
    logger.info("Ensured all predefined roles exist.")