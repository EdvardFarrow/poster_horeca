import datetime
from typing import Optional, List
import requests
from decouple import config
import logging

logger = logging.getLogger(__name__)

class PosterAPIClient:
    api_url = config("POSTER_API_URL")
    api_token = config("POSTER_API_TOKEN")

    def __init__(self, api_token: str = None, api_url: str = None):
        self.api_token = api_token or self.api_token
        self.api_url = api_url or self.api_url

    def _format_date(self, date_str: str) -> str:
            date_only = date_str.split("T")[0]
            return datetime.datetime.strptime(date_only, "%Y-%m-%d").strftime("%Y%m%d")

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
            logger.info(f"Request to {endpoint} with params: {params}")


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

        logger.info(f"Waiters request params: {params}")
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

        logger.info(f"Clients request params: {params}")
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


