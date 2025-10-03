import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
from typing import Optional, List
import requests
from decouple import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Можно поставить INFO, если слишком много данных
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

class PosterAPIClient:
    api_url = config("POSTER_API_URL")
    api_token = config("POSTER_API_TOKEN")

    def __init__(self, api_token: str = None, api_url: str = None):
        self.api_token = api_token or self.api_token
        self.api_url = api_url or self.api_url

    def _format_date(self, date_str: str) -> str:
        if isinstance(date_str, list):
            date_str = date_str[0]
        if len(date_str) == 8 and date_str.isdigit():
            return date_str
        date_only = date_str.split("T")[0]
        return datetime.strptime(date_only, "%Y-%m-%d").strftime("%Y%m%d")

    def make_request(self, method: str, endpoint: str, params: Optional[dict] = None) -> dict:
        try:
            url = f"{self.api_url}{endpoint}"
            params = params or {}
            params["token"] = self.api_token

            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")


            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise Exception(f"API Error: {data['error']}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {"error": str(e)}
        



    # ------------------ Clients ------------------
    def get_clients_sales(self, date_from: str = None, date_to: str = None, spot_id: int = None) -> list[dict]:
        params = {
            "type": "clients",
            "interpolate": "day",
            "business_day": "false",
        }
        if date_from:
            params["dateFrom"] = self._format_date(date_from)
        if date_to:
            params["dateTo"] = self._format_date(date_to)
        if spot_id:
            params["spot_id"] = spot_id

        data = self.make_request("GET", "dash.getAnalytics", params=params).get("response", [])

        normalized = []
        for item in data:
            revenue = int(item.get("revenue", 0)) / 100
            transactions = int(item.get("clients", 0))
            avg_check = revenue / transactions if transactions else 0

            normalized.append({
                "client_id": item.get("client_id"),
                "firstname": item.get("firstname", ""),
                "lastname": item.get("lastname", ""),
                "phone": item.get("phone", ""),
                "name": f"{item.get('lastname', '')} {item.get('firstname', '')} {item.get('phone', '')}".strip(),
                "email": item.get("email", ""),
                "revenue": round(revenue, 2),
                "profit": round(int(item.get("profit", 0)) / 100, 2),
                "transactions": transactions,
                "avg_check": round(avg_check, 2)
            })
        return normalized



    # ------------------ Products ------------------
    def get_products(self, spot_id: int = None) -> list[dict]:
        params = {}
        if spot_id:
            params["spot_id"] = spot_id

        data = self.make_request("GET", "menu.getProducts", params=params).get("response", [])
        normalized = []
        for item in data:
            normalized.append({
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name"),
                "category_id": item.get("menu_category_id"),
                "category_name": item.get("category_name"),
                "cost": float(item.get("cost", 0)),
                "fiscal": bool(item.get("fiscal", True)),
                "workshop": int(item.get("workshop", 0))
            })
        return normalized



    # ------------------ Products Sales------------------
    def get_products_sales(self, date_from: str = None, date_to: str = None, spot_id: int = None) -> List[dict]:
        params = {
            "type": "products",
            "interpolate": "day",
            "business_day": "false",
        }
        if date_from:
            params["dateFrom"] = self._format_date(date_from)
        if date_to:
            params["dateTo"] = self._format_date(date_to)
        if spot_id:
            params["spot_id"] = spot_id

        data = self.make_request("GET", "dash.getProductsSales", params=params).get("response", [])
        normalized = []

        for item in data:
            normalized.append({
                "product_id": item.get("product_id"),
                "name": item.get("product_name"),
                "category_id": item.get("category_id"),
                "category_name": item.get("category_name"),
                "price": int(item.get("price", 0)),
                "count": float(item.get("count", 0)),
                "product_profit": round(int(item.get("product_profit", 0)) / 100, 2)
            })
        return normalized
    
    #--------------Category------------
    def get_category(self, spot_id: int = None) -> list[dict]:
        params = {}
        if spot_id:
            params["spot_id"] = spot_id

        data = self.make_request("GET", "menu.getCategories", params=params).get("response", [])

        return [
            {
                "category_id": el.get("category_id"),
                "name": el.get("category_name"),
            }
            for el in data
        ]


    # ------------------ Categories ------------------
    def get_categories_sales(self, date_from: str = None, date_to: str = None, spot_id: int = None) -> List[dict]:
        params = {
            "type": "categories",
            "interpolate": "day",
            "business_day": "false",
        }
        if date_from:
            params["dateFrom"] = self._format_date(date_from)
        if date_to:
            params["dateTo"] = self._format_date(date_to)
        if spot_id:
            params["spot_id"] = spot_id

        data = self.make_request("GET", "dash.getCategoriesSales", params=params).get("response", [])
        normalized = []

        for item in data:
            normalized.append({
                "category_id": item.get("category_id"),
                "name": item.get("category_name"),
                "count": float(item.get("count", 0)),
                "profit": round(int(item.get("profit", 0)) / 100, 2),
            })
        return normalized


    # ------------------ Reports ------------------
    def _normalize_shift(self, shift: dict) -> dict:
        return {
            "poster_shift_id": shift.get("cash_shift_id"),
            "date_start": shift.get("date_start"),
            "date_end": shift.get("date_end"),
            "amount_start": int(shift.get("amount_start", 0)) / 100,
            "amount_end": int(shift.get("amount_end", 0)) / 100,
            "amount_debit": int(shift.get("amount_debit", 0)) / 100,
            "amount_sell_cash": int(shift.get("amount_sell_cash", 0)) / 100,
            "amount_sell_card": int(shift.get("amount_sell_card", 0)) / 100,
            "amount_credit": int(shift.get("amount_credit", 0)) / 100,
            "amount_collection": int(shift.get("amount_collection", 0)) / 100,
            "user_id_start": shift.get("user_id_start"),
            "user_id_end": shift.get("user_id_end"),
            "comment": shift.get("comment"),
        }

    def get_cash_shifts(self, date_from: str = None, date_to: str = None, spot_id: int = None) -> list[dict]:
        params = {}
        if date_from:
            params["dateFrom"] = self._format_date(date_from)
        if date_to:
            params["dateTo"] = self._format_date(date_to)
        if spot_id:
            params["spot_id"] = int(spot_id)

        response = self.make_request("GET", "finance.getCashShifts", params=params).get("response", [])
        return [self._normalize_shift(shift) for shift in response] if response else []



    
    
    
    def get_transactions(
            self,
            date_from: str,
            date_to: str,
            spot_id: int = None,
            include_products: bool = False,
            include_delivery: bool = False
        ) -> list[dict]:
        params = {
            "dateFrom": self._format_date(date_from),
            "dateTo": self._format_date(date_to),
            "status": 2,  # только закрытые
            "include_products": str(include_products).lower(),
            "include_delivery": str(include_delivery).lower(),
            "type": "spots",
        }
        if spot_id:
            params["id"] = spot_id

        data = self.make_request("GET", "dash.getTransactions", params=params).get("response", [])
        return data

    def get_transactions_products(self, transaction_ids: list[int] = None) -> list[dict]:
        params = {}
        if transaction_ids:
            params["transactions_id"] = ",".join(map(str, transaction_ids))

        data = self.make_request("GET", "dash.getTransactionsProducts", params=params).get("response", [])
        return data

    # ------------------ Асинхронный fetch истории ------------------
    async def fetch_history_limited(self, tx_id: str, sem: asyncio.Semaphore):
        async with sem:
            try:
                history = await asyncio.to_thread(
                    lambda: self.make_request(
                        "GET", "dash.getTransactionHistory", params={"transaction_id": tx_id}
                    )
                )
                actions = history.get("response", [])

                payment_method_id = None
                tip_sum = 0.0 
                
                
                for action in actions:
                    if action.get("type_history") == "close" and action.get("value_text"):
                        try:
                            value_text = json.loads(action["value_text"])
                            payment_method_id = value_text.get("payment_method_id")
                            if payment_method_id is not None:
                                payment_method_id = int(payment_method_id)
                                
                            ts = value_text.get("tip_sum")
                            if ts is None:
                                ts = value_text.get("tip")
                            if ts is not None:
                                try:
                                    tip_sum += float(ts)
                                except Exception:
                                    logger.debug(f"Can't parse tip_sum '{ts}' for tx {tx_id}")    
                            
                            
                        except Exception as e:
                            logger.warning(f"Failed to parse value_text for {tx_id}: {e}")

                return tx_id, actions, payment_method_id, tip_sum


            except Exception as e:
                logger.warning(f"Failed to fetch history for {tx_id}: {e}")
                return tx_id, [], None

    # ------------------ Fetch all histories ------------------
    async def fetch_all_histories(self, transaction_ids: list[str]):
        sem = asyncio.Semaphore(5)
        tasks = [self.fetch_history_limited(tx_id, sem) for tx_id in transaction_ids]
        return await asyncio.gather(*tasks)

    # ------------------ Shift Sales ------------------
    def get_sales_by_shift_with_delivery(self, date: str, spot_id: int = None) -> dict:
        date_from_dt = datetime.strptime(date, "%Y-%m-%d")
        date_to_dt = date_from_dt + timedelta(days=1)
        date_to_dt_limit = date_to_dt.replace(hour=6, minute=0, second=0)

        shifts_data = self.get_cash_shifts(date_from=date, date_to=date, spot_id=spot_id)
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

        date_to_str = (date_from_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        transactions_data = self.get_transactions(
            date_from=date, date_to=date_to_str, spot_id=spot_id,
            include_products=True, include_delivery=True
        )
        if not transactions_data:
            logger.warning("No transactions found")
            return {}

        transaction_ids = [t['transaction_id'] for t in transactions_data]
        histories = asyncio.run(self.fetch_all_histories(transaction_ids))
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

        products_data = self.get_transactions_products(transaction_ids)        

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

        result = {
            shift['id']: {
                'regular': defaultdict(lambda: {'product_id': None, 'product_name': None, 'count': 0, 'product_sum': 0.0, 'payed_sum': 0.0, 'profit': 0.0, 'workshop': None}),
                'delivery': defaultdict(lambda: {'product_id': None, 'product_name': None, 'count': 0, 'product_sum': 0.0, 'payed_sum': 0.0, 'profit': 0.0, 'workshop': None, 'delivery_service': "Другое", 'tips': 0.0}),
                'difference': 0.0,
                'tips': 0.0
            } for shift in shifts
        }

        # Сопоставление времени транзакций
        tx_time_map = {}
        for prod in products_data:
            try:
                tx_id = int(prod.get('transaction_id'))
                if tx_id not in tx_time_map:
                    tx_time_map[tx_id] = datetime.fromtimestamp(int(prod['time']) / 1000)
            except Exception:
                continue

        # Распределяем tips по сменам и сервисам
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

        # Распределяем продукты по сменам
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

        # Считаем разницу и распределяем tips на продукты
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

        
        
        # Формируем финальный результат
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
            

        return final_result




    def get_payments_id(self) -> list[dict]:
        data = self.make_request("GET", "settings.getPaymentMethods").get("response", [])

        return [
            {
                "payment_method_id": el.get("payment_method_id"),
                "title": el.get("title")
            }
            for el in data
        ]


    def get_full_transactions_for_day(self, date_from: str, date_to: str, spot_id: int = None) -> list[dict]:

        transactions = self.get_transactions(date_from=date_from, date_to=date_to, spot_id=spot_id)

        all_close_history = []

        for tx in transactions:
            tx_id = tx.get("transaction_id")
            if not tx_id:
                continue

            history = self.make_request(
                "GET",
                "dash.getTransactionHistory",
                params={"transaction_id": tx_id}
            ).get("response", [])

            close_events = [h for h in history if h.get("type_history") == "close"]
            all_close_history.extend(close_events)

        return all_close_history



    def get_workshop(self) -> list[dict]:
        data = self.make_request("GET", "menu.getWorkshops").get("response", [])

        return [
            {
                "workshop_id": el.get("workshop_id"),
                "workshop_name": el.get("workshop_name"),
                "delete": el.get("delete")
            }
            for el in data
        ]
        
        
        
        
