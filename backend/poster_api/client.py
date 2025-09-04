from collections import defaultdict
from datetime import datetime, timedelta
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
        

    # ------------------ Waiters ------------------
    def get_waiters_sales(self, date_from: str = None, date_to: str = None, spot_id: int = None) -> list[dict]:
        params = {
            "type": "waiters",
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
                "name": item.get("name"),
                "revenue": round(revenue, 2),
                "profit": round(int(item.get("profit", 0)) / 100, 2),
                "transactions": transactions,
                "avg_check": round(avg_check, 2)
            })
        return normalized


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
                "id": item.get("id"),
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
                "name": item.get("product_name"),
                "count": float(item.get("count", 0)),
                "price": int(item.get("price", 0)),
                "product_profit": round(int(item.get("product_profit", 0)) / 100, 2)
            })
        return normalized

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
                "name": item.get("category_name"),
                "count": float(item.get("count", 0)),
                "profit": round(int(item.get("profit", 0)) / 100, 2),
            })
        return normalized


    # ------------------ Reports ------------------
    def get_cash_shifts(self, date_from: str = None, date_to: str = None, spot_id: int = None) -> List[dict]:
        params = {}
        if date_from:
            params["dateFrom"] = self._format_date(date_from)
        if date_to:
            params["dateTo"] = self._format_date(date_to)
        if spot_id:
            params["spot_id"] = int(spot_id)

        response = self.make_request("GET", "finance.getCashShifts", params=params).get("response", [])

        if not response:
            return []

        normalized = []
        for shift in response:
            normalized.append({
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
            })
        return normalized   





    def get_employees(self) -> List[dict]:
        data = self.make_request("GET", "access.getEmployees").get("response", [])
        normalized = []
        
        for emp in data:
            normalized.append({
                "poster_id": emp.get("user_id"),
                "name": emp.get("name"),
                "role_id": emp.get("role_id"),
                "role_name": emp.get("role_name"),
                "phone": emp.get("phone"),
                "access_mask": emp.get("access_mask"),
                "user_type": emp.get("user_type"),
                "last_in": emp.get("last_in"),
            })
        return normalized
    
    
    # ------------------ Transactions ------------------
    def get_transactions(
        self,
        date_from: str,
        date_to: str,
        spot_id: int = None,
        include_products: bool = False,
        include_delivery: bool = False
    ) -> List[dict]:
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


    def get_transactions_products(self, transaction_ids: List[int]) -> List[dict]:
        if not transaction_ids:
            return []

        params = {
            "transactions_id": ",".join(map(str, transaction_ids))
        }
        data = self.make_request("GET", "dash.getTransactionsProducts", params=params).get("response", [])
        return data



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
            if s['date_end'] == '0000-00-00 00:00:00':
                end_dt = datetime.now()
            else:
                end_dt = datetime.strptime(s['date_end'], "%Y-%m-%d %H:%M:%S")
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
            date_from=date,
            date_to=date_to_str,
            spot_id=spot_id,
            include_products=True,
            include_delivery=True
        )
        if not transactions_data:
            logger.warning("No transactions found")
            return {}

        transaction_ids = [t['transaction_id'] for t in transactions_data]

        products_data = self.get_transactions_products(transaction_ids)
        if not products_data:
            logger.warning("No products found")

        result = {
            shift['id']: {
                'regular': defaultdict(lambda: {'product_id': None, 'product_name': None, 'count': 0, 'payed_sum': 0.0, 'profit': 0.0}),
                'delivery': defaultdict(lambda: {'product_id': None, 'product_name': None, 'count': 0, 'payed_sum': 0.0, 'profit': 0.0}),
                'difference': 0.0  
            }
            for shift in shifts
        }

        for product in products_data:
            try:
                product_time = datetime.fromtimestamp(int(product['time']) / 1000)
                mode = int(product.get('service_mode', 1))
                category = 'delivery' if mode == 3 else 'regular'

                assigned = False
                for shift in shifts:
                    if shift['start_dt'] <= product_time <= shift['end_dt']:
                        res = result[shift['id']][category][product['product_id']]
                        if res['product_id'] is None:
                            res['product_id'] = product['product_id']
                            res['product_name'] = product['product_name']
                            res['workshop'] = product.get('workshop')

                        res['count'] += float(product['num'])
                        res['payed_sum'] = round(res['payed_sum'] + float(product.get('payed_sum', 0)), 2)
                        res['product_sum'] = float(product.get('product_sum', 0))
                        res['profit'] += round(float(product.get('product_profit', 0)) / 100, 2)
                        assigned = True
                        break

                # Костыль: учитываем продукты до начала первой смены
                if not assigned and shifts:
                    first_shift = shifts[0]
                    first_shift_start = first_shift['start_dt']

                    early_morning_start = first_shift_start.replace(hour=9, minute=0, second=0)
                    if early_morning_start <= product_time < first_shift_start:
                        res = result[first_shift['id']][category][product['product_id']]
                        if res['product_id'] is None:
                            res['product_id'] = product['product_id']
                            res['product_name'] = product['product_name']
                            res['workshop'] = product.get('workshop')

                        res['count'] += float(product['num'])
                        res['payed_sum'] = round(res['payed_sum'] + float(product.get('payed_sum', 0)), 2)
                        res['product_sum'] = float(product.get('product_sum', 0))
                        res['profit'] += round(float(product.get('product_profit', 0)) / 100, 2)
                        assigned = True


            except Exception as e:
                logger.error(f"Error processing product {product}: {e}")

        for shift in shifts:
            shift_id = shift['id']
            regular_sum = sum(p['payed_sum'] for p in result[shift_id]['regular'].values())
            delivery_sum = sum(p['payed_sum'] for p in result[shift_id]['delivery'].values())
            total_sales = round(regular_sum + delivery_sum, 2)
            difference = round(shift['total_payments'] - total_sales, 2)
            result[shift_id]['difference'] = round(shift['total_payments'] - total_sales, 2)
            
            

        final_result = {}
        for shift_id, sales in result.items():
            final_result[shift_id] = {
                'regular': list(sales['regular'].values()),
                'delivery': list(sales['delivery'].values()),
                'difference': sales['difference']  
            }

        return final_result
