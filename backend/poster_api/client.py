import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import json
from typing import Optional, List
import requests
from decouple import config
import logging
from .decorators import timing_decorator

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    
    
REGULAR_PAYMENT_IDS = {0, 1, 2, 3, 4, 5}
SERVICE_MAP = {
    7: "Uber Eats", 
    8: "Wolt", 
    9: "Just Eat", 
    10: "Glovo CASH",
    11: "Wolt", 
    12: "Glovo CARD", 
    13: "Bolt"
}



class PosterAPIClient:
    api_url = config("POSTER_API_URL")
    api_token = config("POSTER_API_TOKEN")

    def __init__(self, api_token: str = None, api_url: str = None):
        self.api_token = api_token or self.api_token
        self.api_url = api_url or self.api_url

    def _format_date(self, date_str: str) -> str:
        """This helper method is designed to be robust against common "dirty"
    date inputs. It handles:
        - ISO-formatted strings (e.g., "2025-10-18T10:00:00"), stripping the time.
        - Simple date strings (e.g., "2025-10-18").
        - Strings that are already in the target "YYYYMMDD" format (idempotency).
        - Inputs that are incorrectly passed as a single-element list.

        Args:
            date_str (str): The input date. Can be in 'YYYY-MM-DD',
            'YYYY-MM-DDTHH:MM:SS', or 'YYYYMMDD' format.

        Returns:
            str: The date string formatted as 'YYYYMMDD'.
        """
        if isinstance(date_str, list):
            date_str = date_str[0]
        if len(date_str) == 8 and date_str.isdigit():
            return date_str
        date_only = date_str.split("T")[0]
        return datetime.strptime(date_only, "%Y-%m-%d").strftime("%Y%m%d")


    # --- Request ---
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


    # --- Clients ---
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


    # --- Products ---
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


    # --- Products Sales ---
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
    
    
    #--- Category ---
    def get_category(self, spot_id: int = None) -> list[dict]:
        params = {}
        if spot_id:
            params["spot_id"] = spot_id

        data = self.make_request("GET", "menu.getCategories", params=params).get("response", [])

        return [
            {
                "category_id": el.get("category_id"),
                "category_name": el.get("category_name"),
            }
            for el in data
        ]


    # --- Categories Sales ---
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


    # --- Reports ---
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


    # --- CASH Shifts ---
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


    # --- Transactions ---
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
            "status": 2,  # close only
            "include_products": str(include_products).lower(),
            "include_delivery": str(include_delivery).lower(),
            "type": "spots",
        }
        if spot_id:
            params["id"] = spot_id

        data = self.make_request("GET", "dash.getTransactions", params=params).get("response", [])
        return data


    # --- Transactions Products ---
    def get_transactions_products(self, transaction_ids: list[int] = None) -> list[dict]:
        params = {}
        if transaction_ids:
            params["transactions_id"] = ",".join(map(str, transaction_ids))

        data = self.make_request("GET", "dash.getTransactionsProducts", params=params).get("response", [])
        return data

    # --- Async history fetch ---
    async def fetch_history_limited(self, tx_id: str, sem: asyncio.Semaphore):
        """This method uses a semaphore to limit concurrent API requests. It fetches
        the transaction history and iterates through its actions to find a 'close'
        event. From this event, it attempts to parse a JSON payload
        ('value_text') to extract the 'payment_method_id' and the 'tip_sum'.
        It handles potential errors during parsing and fetching.

        Args:
            tx_id (str): The unique identifier for the transaction.
            sem (asyncio.Semaphore): A semaphore to control concurrency of network requests.

        Returns:
            tuple[str, list, int | None, float]: A tuple containing:
                - The original transaction ID (tx_id).
                - The list of history actions (or an empty list on failure).
                - The parsed payment_method_id (int) or None if not found/failed.
                - The parsed tip_sum (float), defaulting to 0.0.
        """
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
        """This method manage the fetching of all transaction histories
        in parallel. It initializes an asyncio.Semaphore with a fixed limit (5)
        to manage the load on the external API and then uses asyncio.gather
        to execute all fetch operations.

        Args:
            transaction_ids (list[str]): A list of transaction IDs to fetch.

        Returns:
            list[tuple]: A list where each element is the tuple result from fetch_history_limited().
        """
        sem = asyncio.Semaphore(5)
        tasks = [self.fetch_history_limited(tx_id, sem) for tx_id in transaction_ids]
        return await asyncio.gather(*tasks)

    # ------------------ Shift Sales ------------------
    @timing_decorator
    def get_sales_by_shift_with_delivery(self, date: str, spot_id: int = 1) -> dict:
        """This comprehensive method orchestrates several data fetches to build a
        detailed sales report for a given date. A "business day" is defined as
        running until 6:00 AM the following day.

        The process is as follows:
        1.  Fetches all cash shifts for the given `date` and `spot_id`.
        2.  Fetches all transactions (including products and delivery info) for
            the relevant time period (from the given date to the next day).
        3.  Asynchronously fetches transaction histories to get payment method
            IDs and tip amounts for each transaction.
        4.  Fetches all individual products (line items) from those transactions.
        5.  Maps each product to its correct cash shift using its timestamp.
            Includes special logic to assign pre-shift sales (e.g., after 9 AM
            but before the first shift's official start) to the first shift.
        6.  Aggregates products into two main categories: 'regular' (sales
            made via standard payment methods) and 'delivery' (sales made via
            delivery service payment methods).
        7.  'Delivery' sales are further sub-aggregated by both product_id
            and the specific delivery service (e.g., Wolt, Glovo).
        8.  Processes and assigns all tips to their respective shift and service.
        9.  Calculates the 'difference' (discrepancy) between the shift's
            reported total (cash + card) and the sum of all aggregated
            'payed_sum' values from transactions.

        Args:
            date (str): The target date in 'YYYY-MM-DD' format.
            spot_id (int, optional): The spot/location identifier. Defaults to 1.

        Returns:
            dict: A dictionary keyed by shift IDs. Each value is a dictionary
            containing:
                - 'regular' (list): Sorted list of aggregated regular sales items.
                - 'delivery' (list): Sorted list of aggregated delivery items.
                - 'difference' (float): Discrepancy between shift total and transaction sum.
                - 'tips_by_service' (dict): A breakdown of tips by service name.
                - 'tips' (float): Total tips for the shift.
        """
        date_from_dt = datetime.strptime(date, "%Y-%m-%d")
        date_to_dt_limit = (date_from_dt + timedelta(days=1)).replace(hour=6, minute=0, second=0)
        shifts_data = self.get_cash_shifts(date_from=date, date_to=date, spot_id=spot_id)
        if not shifts_data:
            logger.warning(f"Смены за {date} не найдены.")
            return {}
        shifts = []
        for s in shifts_data:
            start_dt = datetime.strptime(s['date_start'], "%Y-%m-%d %H:%M:%S")
            end_dt_str = s.get('date_end', '0000-00-00 00:00:00')
            end_dt = datetime.now() if end_dt_str == '0000-00-00 00:00:00' else datetime.strptime(end_dt_str, "%Y-%m-%d %H:%M:%S")
            shifts.append({
                'id': s['poster_shift_id'],
                'start_dt': start_dt,
                'end_dt': min(end_dt, date_to_dt_limit),
                'total_payments': round((s.get("amount_sell_cash", 0) or 0) + (s.get("amount_sell_card", 0) or 0), 2)
            })
        shifts.sort(key=lambda x: x['start_dt'])

        date_to_str = (date_from_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        transactions_data = self.get_transactions(
            date_from=date, date_to=date_to_str, spot_id=spot_id,
            include_products=True, include_delivery=True
        )
        if not transactions_data:
            logger.warning(f"Транзакции за {date} не найдены.")
            return {}
        transaction_ids = [t['transaction_id'] for t in transactions_data if t.get('transaction_id')]
        transactions_map = {int(t['transaction_id']): t for t in transactions_data if t.get('transaction_id')}
        histories = asyncio.run(self.fetch_all_histories(transaction_ids))
        payment_map, tips_map = {}, {}
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

        first_shift_early_start = shifts[0]['start_dt'].replace(hour=9, minute=0, second=0) if shifts else None
        def _find_shift_id(timestamp: datetime) -> int | None:
            for shift in shifts:
                if shift['start_dt'] <= timestamp <= shift['end_dt']: return shift['id']
            if first_shift_early_start and first_shift_early_start <= timestamp < shifts[0]['start_dt']: return shifts[0]['id']
            return None
        result = { shift['id']: {'regular': defaultdict(dict), 'delivery': defaultdict(dict)} for shift in shifts }
        for product in products_data:
            try:
                tx_id = int(product['transaction_id']); product_time = datetime.fromtimestamp(int(product['time']) / 1000)
            except (ValueError, TypeError, KeyError):
                continue 
            shift_id = _find_shift_id(product_time)
            if not shift_id: continue
            payment_id = payment_map.get(tx_id)
            is_delivery = payment_id not in REGULAR_PAYMENT_IDS
            category = 'delivery' if is_delivery else 'regular'
            key = product['product_id']
            if is_delivery:
                service_name = SERVICE_MAP.get(payment_id, "Другое"); key = (product['product_id'], service_name)
            agg_data = result[shift_id][category][key]
            if not agg_data:
                agg_data['product_id'] = product['product_id']; agg_data['product_name'] = product['product_name']
                agg_data['workshop'] = product.get('workshop')
                agg_data.update({'count': 0.0, 'product_sum': 0.0, 'payed_sum': 0.0, 'profit': 0.0, 'tips': 0.0})
                if is_delivery: agg_data['delivery_service'] = service_name
            agg_data['count'] += float(product.get('num', 0))
            agg_data['product_sum'] += float(product.get('product_sum', 0))
            agg_data['payed_sum'] += round(float(product.get('payed_sum', 0)), 2)
            agg_data['profit'] += round(float(product.get('product_profit', 0)) / 100, 2)
        
        
        tx_time_map = {}
        for prod in products_data:
            try:
                tx_id = int(prod.get('transaction_id'))
                if tx_id not in tx_time_map:
                    tx_time_map[tx_id] = datetime.fromtimestamp(int(prod['time']) / 1000)
            except Exception:
                continue
            
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
            service_name = SERVICE_MAP.get(payment_id_int, "Другое")
            tips_by_shift_service[found_shift_id][service_name] += tip

        final_result = {}
        for shift in shifts:
            sid = shift['id']
            sales = result[sid]
            
            regular_sales = list(sales['regular'].values())
            delivery_sales = list(sales['delivery'].values())
            
            service_tips_for_shift = tips_by_shift_service.get(sid, {})
            for service, tip_sum in service_tips_for_shift.items():
                for entry in delivery_sales:
                    if entry.get('delivery_service') == service:
                        entry['tips'] += round(tip_sum, 2)
                        break
            
            regular_sum = sum(p['payed_sum'] for p in regular_sales)
            delivery_sum = sum(p['payed_sum'] for p in delivery_sales)
            
            final_result[sid] = {
                'regular': sorted(regular_sales, key=lambda x: x.get('product_name', '')),
                'delivery': sorted(delivery_sales, key=lambda x: x.get('product_name', '')),
                'difference': round(shift['total_payments'] - (regular_sum + delivery_sum), 2),
                'tips_by_service': dict(tips_by_shift_service[sid]),
                'tips': sum(tips_by_shift_service[sid].values())
            }

        return final_result



    # --- Payments id ---
    def get_payments_id(self) -> list[dict]:
        data = self.make_request("GET", "settings.getPaymentMethods").get("response", [])

        return [
            {
                "payment_method_id": el.get("payment_method_id"),
                "title": el.get("title")
            }
            for el in data
        ]


    # --- Transactions for day ---
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


    # --- Workshops ---
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


    # --- Spots ---
    def get_spots(self) -> list[dict]:
        data = self.make_request('GET', 'spots.getSpots').get('response', [])
        
        return [
            {
                'spot_id': el.get('spot_id'),
                'spot_name': el.get('name'),
                'spot_address': el.get('address'),
            }
            for el in data
        ]