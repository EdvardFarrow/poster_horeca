from typing import Any, Optional, Union, List
import requests
from decouple import config
import logging

logger = logging.getLogger(__name__)


class PosterAPIClient:
    api_url = config('POSTER_API_URL')
    api_token = config('POSTER_API_TOKEN')
    fiscal = 0

    def __init__(self, api_token: str = None, api_url: str = None, fiscal: int = 0) -> None:
        self.api_token = api_token or self.api_token
        self.api_url = api_url or self.api_url
        self.fiscal = fiscal

    def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> dict:
        try:
            url = f"{self.api_url}{endpoint}"
            params = params or {}
            params['token'] = self.api_token

            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, json=json_data)
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

    def get_analytics(
        self,
        select: Union[str, List[str]] = "revenue",
        type_: str = "waiters",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        entity_id: Optional[int] = None,
        interpolate: str = "day",
        business_day: bool = False,
    ) -> list[dict]:

        if isinstance(select, list):
            select_str = ",".join(select)
        else:
            select_str = select

        params = {
            "select": select_str,
            "type": type_,
            "fiscal": self.fiscal,
            "interpolate": interpolate,
            "business_day": business_day
        }
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if entity_id:
            params["id"] = entity_id

        raw_data = self.make_request("GET", "dash.getAnalytics", params=params)
        response = raw_data.get("response", [])

        return self._normalize_response(response, type_, interpolate, select)

    def _normalize_response(self, response: Any, type_: str, interpolate: str, select: Union[str, List[str]]) -> list[dict]:
        normalized = []

        if isinstance(select, str):
            select_list = [select]
        else:
            select_list = select

        def add_period(item: dict) -> dict:
            period_key_map = {
                "day": "date",
                "week": "week",
                "month": "month"
            }
            key = period_key_map.get(interpolate)
            if key and key in item:
                item["period"] = item[key]
            return item

        if type_ == "waiters":
            for item in response:
                entry = {
                    "id": item.get("user_id"),
                    "name": item.get("name"),
                }
                if "revenue" in select_list:
                    entry["revenue"] = item.get("revenue")
                if "profit" in select_list:
                    entry["profit"] = item.get("profit")
                if "transactions" in select_list:
                    entry["transactions"] = item.get("clients")
                if "avg_time" in select_list:
                    entry["avg_time"] = item.get("middle_time")

                normalized.append(add_period(entry))

        elif type_ == "clients":
            for item in response:
                entry = {
                    "id": item.get("client_id"),
                    "name": f"{item.get('firstname', '')} {item.get('lastname', '')}".strip(),
                    "phone": item.get("phone"),
                    "email": item.get("email"),
                }
                if "revenue" in select_list:
                    entry["revenue"] = item.get("revenue")
                if "profit" in select_list:
                    entry["profit"] = item.get("profit")
                if "transactions" in select_list:
                    entry["transactions"] = item.get("clients")
                if "payed_cash" in select_list:
                    entry["payed_cash"] = item.get("payed_cash")
                if "payed_card" in select_list:
                    entry["payed_card"] = item.get("payed_card")
                if "payed_third_party" in select_list:
                    entry["payed_third_party"] = item.get("payed_third_party")

                normalized.append(add_period(entry))

        elif type_ in ("workshops", "category", "products", "spots"):
            if isinstance(response, list) and response:
                counters = response[0].get("counters", {})
            elif isinstance(response, dict):
                counters = response.get("counters", {})
            else:
                counters = {}

            entry = {}
            for metric in select_list:
                entry[metric] = counters.get(metric)
            normalized.append(add_period(entry))

        else:
            normalized = [add_period(item) if isinstance(item, dict) else item for item in response]

        return normalized
