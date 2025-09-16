import json
import logging
from backend.poster_api.models import TransactionHistory, Transactions




logger = logging.getLogger(__name__)


def parse_transaction_history_from_db(transaction_id: int):
    """
    Берет историю транзакции из БД и возвращает payment_method_id, tip_sum и все actions
    """
    try:
        transaction = Transactions.objects.get(transaction_id=transaction_id)
    except Transactions.DoesNotExist:
        return {
            "tx_id": transaction_id,
            "actions": [],
            "payment_method_id": None,
            "tip_sum": 0.0
        }

    actions_qs = TransactionHistory.objects.filter(transaction=transaction)
    actions = list(actions_qs.values())  

    payment_method_id = None
    tip_sum = 0.0

    for action in actions:
        if action.get("type_history") == "close" and action.get("value_text"):
            try:
                value_text = action["value_text"]
                if isinstance(value_text, str):
                    value_text = json.loads(value_text)

                pm_id = value_text.get("payment_method_id")
                if pm_id is not None:
                    payment_method_id = int(pm_id)

                ts = value_text.get("tip_sum") or value_text.get("tip")
                if ts is not None:
                    tip_sum += float(ts)
            except Exception as e:
                logger.warning(f"Failed to parse value_text for {transaction_id}: {e}")

    return {
        "tx_id": transaction_id,
        "actions": actions,
        "payment_method_id": payment_method_id,
        "tip_sum": tip_sum
    }



def parse_all_histories_from_db(transaction_ids: list[int]):
    """
    Парсим историю сразу для списка транзакций
    """
    results = []
    for tx_id in transaction_ids:
        parsed = parse_transaction_history_from_db(tx_id)
        results.append(parsed)
    return results



# aggregation.py
import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Aggregator:
    def __init__(self, client):
        """
        client - объект, у которого есть методы:
        get_cash_shifts, get_transactions, get_transactions_products, fetch_history_limited
        """
        self.client = client

    async def fetch_all_histories(self, transaction_ids: list[str]):
        """Асинхронный запуск fetch_history_limited с ограничением семафором"""
        sem = asyncio.Semaphore(5)
        tasks = [self.client.fetch_history_limited(tx_id, sem) for tx_id in transaction_ids]
        return await asyncio.gather(*tasks)

    def get_sales_by_shift_with_delivery(self, date: str, spot_id: int = None) -> dict:
        """Основной метод агрегации продаж по сменам с учётом доставки и чаевых"""
        date_from_dt = datetime.strptime(date, "%Y-%m-%d")
        date_to_dt = date_from_dt + timedelta(days=1)
        date_to_dt_limit = date_to_dt.replace(hour=6, minute=0, second=0)

        # --- Получение смен ---
        shifts_data = self.client.get_cash_shifts(date_from=date, date_to=date, spot_id=spot_id)
        if not shifts_data:
            logger.warning("No shifts found")
            return {}

        shifts = []
        for s in shifts_data:
            start_dt = datetime.strptime(s['date_start'], "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.now() if s['date_end'] == '0000-00-00 00:00:00' else datetime.strptime(s['date_end'], "%Y-%m-%d %H:%M:%S")
            if end_dt > date_to_dt_limit:
                end_dt = date_to_dt_limit
            shifts.append({
                'id': s['poster_shift_id'],
                'start_dt': start_dt,
                'end_dt': end_dt,
                'total_payments': round((s.get("amount_sell_cash", 0) or 0) + (s.get("amount_sell_card", 0) or 0), 2)
            })

        # --- Получение транзакций ---
        date_to_str = (date_from_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        transactions_data = self.client.get_transactions(
            date_from=date, date_to=date_to_str, spot_id=spot_id,
            include_products=True, include_delivery=True
        )
        if not transactions_data:
            logger.warning("No transactions found")
            return {}

        transaction_ids = [t['transaction_id'] for t in transactions_data]
        histories = asyncio.run(self.fetch_all_histories(transaction_ids))

        # --- Создание карт для payment и tips ---
        payment_map = {}
        tips_map = {}
        for entry in histories:
            try:
                tx_id, _, payment_method_id, tip_sum = entry
            except ValueError:
                tx_id, _, payment_method_id = entry
                tip_sum = 0.0
            try:
                tx_int = int(tx_id)
            except Exception:
                continue
            payment_map[tx_int] = int(payment_method_id) if payment_method_id is not None else None
            tips_map[tx_int] = float(tip_sum or 0.0)

        # --- Получение продуктов по транзакциям ---
        products_data = self.client.get_transactions_products(transaction_ids)        

        regular_payment_id = (0, 1, 2, 3, 4, 5)
        service_map = {
            7: "Uber Eats",
            8: "Wolt",
            9: "Just Eat",
            10: "Glovo CASH",
            11: "Wolt",
            12: "Glovo CARD",
            13: "Bolt"
        }

        # --- Инициализация результата по сменам ---
        result = {
            shift['id']: {
                'regular': defaultdict(lambda: {'product_id': None, 'product_name': None, 'count': 0, 'product_sum': 0.0, 'payed_sum': 0.0, 'profit': 0.0, 'workshop': None}),
                'delivery': defaultdict(lambda: {'product_id': None, 'product_name': None, 'count': 0, 'product_sum': 0.0, 'payed_sum': 0.0, 'profit': 0.0, 'workshop': None, 'delivery_service': "Другое", 'tips': 0.0}),
                'difference': 0.0,
                'tips': 0.0
            } for shift in shifts
        }

        # --- Сопоставление времени транзакций ---
        tx_time_map = {}
        for prod in products_data:
            try:
                tx_id = int(prod.get('transaction_id'))
                if tx_id not in tx_time_map:
                    tx_time_map[tx_id] = datetime.fromtimestamp(int(prod['time']) / 1000)
            except Exception:
                continue

        # --- Распределяем tips по сменам и сервисам ---
        tips_by_shift_service = {shift['id']: defaultdict(float) for shift in shifts}
        for tx_id, tip in tips_map.items():
            if not tip:
                continue
            tx_time = tx_time_map.get(tx_id)
            if not tx_time:
                tx_obj = next((t for t in transactions_data if str(t.get('transaction_id')) == str(tx_id)), None)
                if tx_obj:
                    possible = tx_obj.get('time') or tx_obj.get('date') or tx_obj.get('created_at')
                    if possible:
                        try:
                            tx_time = datetime.fromtimestamp(int(possible) / 1000)
                        except Exception:
                            tx_time = None
            if not tx_time:
                continue

            found_shift_id = None
            for shift in shifts:
                if shift['start_dt'] <= tx_time <= shift['end_dt']:
                    found_shift_id = shift['id']
                    break
            if not found_shift_id and shifts:
                first_shift = shifts[0]
                early_morning_start = first_shift['start_dt'].replace(hour=9, minute=0, second=0)
                if early_morning_start <= tx_time < first_shift['start_dt']:
                    found_shift_id = first_shift['id']

            if not found_shift_id:
                continue

            payment_id = payment_map.get(tx_id)
            try:
                payment_id_int = int(payment_id) if payment_id is not None else None
            except Exception:
                payment_id_int = None
            service_name = service_map.get(payment_id_int, "Другое")
            tips_by_shift_service[found_shift_id][service_name] += tip

        # --- Распределяем продукты по сменам ---
        for product in products_data:
            try:
                product_time = datetime.fromtimestamp(int(product['time']) / 1000)
                tx_payment_id = payment_map.get(int(product['transaction_id']))
                category = "regular" if tx_payment_id in regular_payment_id else "delivery"

                if category == "delivery":
                    try:
                        tx_payment_id_int = int(tx_payment_id)
                    except (TypeError, ValueError):
                        tx_payment_id_int = None
                    product['delivery_service'] = service_map.get(tx_payment_id_int, "Другое")

                assigned = False
                for shift in shifts:
                    if shift['start_dt'] <= product_time <= shift['end_dt']:
                        key = f"{product['product_id']}_{product['delivery_service']}" if category == 'delivery' else product['product_id']
                        res = result[shift['id']][category][key]
                        if res['product_id'] is None:
                            res['product_id'] = product['product_id']
                            res['product_name'] = product['product_name']
                            res['workshop'] = product.get('workshop')
                            if category == "delivery":
                                res['delivery_service'] = product['delivery_service']

                        res['count'] += float(product['num'])
                        res['product_sum'] += float(product.get('product_sum', 0))
                        res['payed_sum'] += round(float(product.get('payed_sum', 0)), 2)
                        res['profit'] += round(float(product.get('product_profit', 0)) / 100, 2)
                        assigned = True
                        break

                if not assigned and shifts:
                    first_shift = shifts[0]
                    first_shift_start = first_shift['start_dt']
                    early_morning_start = first_shift_start.replace(hour=9, minute=0, second=0)
                    if early_morning_start <= product_time < first_shift_start:
                        key = f"{product['product_id']}_{product['delivery_service']}" if category == 'delivery' else product['product_id']
                        res = result[first_shift['id']][category][key]
                        if res['product_id'] is None:
                            res['product_id'] = product['product_id']
                            res['product_name'] = product['product_name']
                            res['workshop'] = product.get('workshop')
                            if category == "delivery":
                                res['delivery_service'] = product['delivery_service']

                        res['count'] += float(product['num'])
                        res['product_sum'] += float(product.get('product_sum', 0))
                        res['payed_sum'] += round(float(product.get('payed_sum', 0)), 2)
                        res['profit'] += round(float(product.get('product_profit', 0)) / 100, 2)

            except Exception as e:
                logger.error(f"Error processing product {product}: {e}")

        # --- Считаем разницу и распределяем tips ---
        for shift in shifts:
            sid = shift['id']
            regular_sum = sum(p['payed_sum'] for p in result[sid]['regular'].values())
            delivery_sum = sum(p['payed_sum'] for p in result[sid]['delivery'].values())
            total_sales = round(regular_sum + delivery_sum, 2)
            result[sid]['difference'] = round(shift['total_payments'] - total_sales, 2)

            # Присвоение tips
            service_tips = tips_by_shift_service.get(sid, {})
            for entry in result[sid]['delivery'].values():
                entry.setdefault('tips', 0.0)
            for service, tip_sum in service_tips.items():
                assigned = False
                for entry in result[sid]['delivery'].values():
                    if entry.get('delivery_service') == service:
                        entry['tips'] += round(float(tip_sum), 2)
                        assigned = True
                        break
                if not assigned:
                    key = f"service_total_{service}"
                    result[sid]['delivery'][key] = {
                        'product_id': None,
                        'product_name': "",
                        'count': 0,
                        'product_sum': 0.0,
                        'payed_sum': 0.0,
                        'profit': 0.0,
                        'workshop': None,
                        'delivery_service': service,
                        'tips': round(float(tip_sum), 2),
                    }

            result[sid]['tips'] = round(sum(entry.get('tips', 0.0) for entry in result[sid]['delivery'].values()), 2)

        # --- Формируем финальный результат ---
        final_result = {}
        for shift_id, sales in result.items():
            tips_by_service = {}
            for entry in sales['delivery'].values():
                service = entry.get('delivery_service', 'Другое')
                tips_by_service[service] = tips_by_service.get(service, 0.0) + entry.get('tips', 0.0)

            final_result[shift_id] = {
                'regular': sorted(list(sales['regular'].values()), key=lambda x: x['product_name'] or ""),
                'delivery': sorted(list(sales['delivery'].values()), key=lambda x: x['product_name'] or ""),
                'difference': sales['difference'],
                'tips': sales['tips'],
                'tips_by_service': tips_by_service
            }

            logger.debug(
                "SHIFT %s - DELIVERY: %s, TIPS: %s",
                shift_id,
                json.dumps(final_result[shift_id]['delivery'], ensure_ascii=False)[:2000],
                final_result[shift_id]['tips'],
            )

        return final_result
