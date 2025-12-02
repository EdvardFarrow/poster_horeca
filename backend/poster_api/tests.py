from decimal import Decimal
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import date, datetime
from django.urls import reverse
import requests
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
import asyncio
from .client import PosterAPIClient 
from django.utils import timezone
from poster_api.models import (
    ShiftSale, ShiftSaleItem, CashShiftReport, Category, Product,
    ProductSales, CategoriesSales, Clients, Transactions,
    TransactionsProducts, TransactionHistory, Workshop, Payments_ID, Spot
)
from users.models import Role, User
from poster_api.services.saving import (
    save_shift_sales_to_db,
    save_cash_shifts_range,
    save_products,
    save_products_sales,
    save_categories,
    save_categories_sales,
    save_transactions,
    save_transactions_products,
    save_transaction_history,
    save_workshop,
    save_payments_id,
    save_clients,
    sync_all_from_date,
    parse_poster_datetime,
    create_role_lists
)


class TestPosterAPIClient(unittest.TestCase):

    def setUp(self):
        self.api_url = "https://joinposter.com/api/"
        self.api_token = "fake_token"
        self.client = PosterAPIClient(api_token=self.api_token, api_url=self.api_url)

    @patch('poster_api.client.requests.get')
    def test_make_request_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": [{"id": 1, "name": "Test"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.make_request("GET", "some.endpoint", params={"param": "value"})
        
        expected_url = f"{self.api_url}some.endpoint"
        expected_params = {"param": "value", "token": self.api_token}
        mock_get.assert_called_once_with(expected_url, params=expected_params)
        
        self.assertEqual(result, {"response": [{"id": 1, "name": "Test"}]})

    @patch('poster_api.client.requests.get')
    def test_make_request_http_error(self, mock_get):
        error_message = "404 Client Error: Not Found"
        mock_get.side_effect = requests.exceptions.HTTPError(error_message)

        result = self.client.make_request("GET", "some.endpoint")

        self.assertIn("error", result)
        self.assertEqual(result["error"], error_message)


    @patch('poster_api.client.requests.post')
    def test_make_request_post_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Created"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.make_request("POST", "some.endpoint", params={"data": "payload"})

        expected_url = f"{self.api_url}some.endpoint"
        expected_params = {"data": "payload", "token": self.api_token}
        
        mock_post.assert_called_once_with(expected_url, params=expected_params)
        self.assertEqual(result, {"response": "Created"})

    @patch('poster_api.client.requests.get')
    def test_make_request_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid token"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.make_request("GET", "some.endpoint")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "API Error: Invalid token")

    def test_make_request_invalid_method(self):
        result = self.client.make_request("PUT", "some.endpoint")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Unsupported HTTP method: PUT")

    @patch('poster_api.client.requests.get')
    def test_make_request_network_error(self, mock_get):
        error_message = "Connection timed out"
        mock_get.side_effect = requests.exceptions.RequestException(error_message)

        result = self.client.make_request("GET", "some.endpoint")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], error_message)

    def test_format_date(self):
        self.assertEqual(self.client._format_date("2025-10-12T10:00:00"), "20251012")
        self.assertEqual(self.client._format_date("20251012"), "20251012")
        self.assertEqual(self.client._format_date(["2025-10-12"]), "20251012")

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_clients_sales_normalization(self, mock_make_request):
        raw_api_response = {
            "response": [
                {
                    "client_id": 101,
                    "firstname": "John",
                    "lastname": "Doe",
                    "phone": "12345",
                    "email": "john@doe.com",
                    "revenue": 15050,  
                    "profit": 7025,                    
                    "clients": 5,      
                }
            ]
        }
        mock_make_request.return_value = raw_api_response

        result = self.client.get_clients_sales(date_from="2025-10-12")
        
        mock_make_request.assert_called_once_with(
            "GET",
            "dash.getAnalytics",
            params={
                "type": "clients",
                "interpolate": "day",
                "business_day": "false",
                "dateFrom": "20251012"
            }
        )

        self.assertEqual(len(result), 1)
        client_data = result[0]
        self.assertEqual(client_data['client_id'], 101)
        self.assertEqual(client_data['name'], "Doe John 12345")
        self.assertEqual(client_data['revenue'], 150.50) 
        self.assertEqual(client_data['profit'], 70.25)   
        self.assertEqual(client_data['transactions'], 5)
        self.assertEqual(client_data['avg_check'], 30.10) 

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_products_sales_empty_response(self, mock_make_request):
        mock_make_request.return_value = {"response": []}
        
        result = self.client.get_products_sales()

        self.assertEqual(result, [])
        
    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_products(self, mock_make_request):
        raw_api_response = {
            "response": [ 
                {
                    "product_id": 600,
                    "product_name": "Chicken Soup",
                    "menu_category_id": 18,
                    "category_name": "Кухня",
                    "cost": 720,
                    "fiscal": 1,
                    "workshop": 2
                }
            ]
        }
        mock_make_request.return_value = raw_api_response

        result = self.client.get_products(spot_id=1)
        
        expected_result =  [
                {
                    "product_id": 600,
                    "product_name": "Chicken Soup",
                    "category_id": 18,
                    "category_name": "Кухня",
                    "cost": 720.0,
                    "fiscal": True,
                    "workshop": 2
                }
            ]
        
        
        self.assertEqual(result, expected_result)
        
        mock_make_request.assert_called_once_with(
            "GET",
            "menu.getProducts",
            params={"spot_id": 1}
        )
        
    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_products_sales_normalization(self, mock_make_request):
        raw_api_response = {
            "response": [
                {
                    "product_id": 600,
                    "product_name": "Chicken Soup",
                    "category_id": 18,
                    "category_name": "Кухня",
                    "price": 720,
                    "count": 1,
                    "product_profit": 720
                }
            ]
        }
            
        mock_make_request.return_value = raw_api_response

        result = self.client.get_products_sales(date_from="2025-10-12")
        
        mock_make_request.assert_called_once_with(
            "GET",
            "dash.getProductsSales",
            params={
                "type": "products",
                "interpolate": "day",
                "business_day": "false",
                "dateFrom": "20251012"
            }
        )
        
        self.assertEqual(len(result), 1)
        products_sales = result[0]
        self.assertEqual(products_sales['product_id'], 600)
        self.assertEqual(products_sales['name'], "Chicken Soup")
        self.assertEqual(products_sales['category_id'], 18) 
        self.assertEqual(products_sales['category_name'], "Кухня")   
        self.assertEqual(products_sales['price'], 720)
        self.assertEqual(products_sales['count'], 1) 
        self.assertEqual(products_sales['product_profit'], 7.2) 
        
    
    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_category_success(self, mock_make_request):
        mock_make_request.return_value = {
            "response": [
                {"category_id": 19, "category_name": "Кухня"},
                {"category_id": 5, "category_name": "Бар"}
            ]
        }
        
        expected = [
            {"category_id": 19, "category_name": "Кухня"},
            {"category_id": 5, "category_name": "Бар"}
        ]
        result = self.client.get_category(spot_id=1)

        self.assertEqual(result, expected)
        mock_make_request.assert_called_once_with("GET", "menu.getCategories", params={"spot_id": 1})

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_category_empty(self, mock_make_request):
        mock_make_request.return_value = {"response": []}
        self.assertEqual(self.client.get_category(), [])

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_categories_sales_success(self, mock_make_request):
        mock_make_request.return_value = {
            "response": [
                {"category_id": 19, "category_name": "Кухня", "count": 10.0, "profit": 50050}
            ]
        }

        expected = [
            {"category_id": 19, "name": "Кухня", "count": 10.0, "profit": 500.50}
        ]
        result = self.client.get_categories_sales(date_from="2025-10-12")
        
        self.assertEqual(result, expected)
        mock_make_request.assert_called_once_with(
            "GET", "dash.getCategoriesSales", 
            params={
                "type": "categories", "interpolate": "day", "business_day": "false",
                "dateFrom": "20251012"
            }
        )

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_cash_shifts_success(self, mock_make_request):
        mock_make_request.return_value = {
            "response": [{
                "cash_shift_id": 123, "date_start": "2025-10-12 09:00:00", "date_end": "2025-10-12 18:00:00",
                "amount_start": 10000, "amount_end": 50000, "amount_sell_cash": 40000
            }]
        }

        expected = [{
            "poster_shift_id": 123, "date_start": "2025-10-12 09:00:00", "date_end": "2025-10-12 18:00:00",
            "amount_start": 100.00, "amount_end": 500.00, "amount_sell_cash": 400.00,
            "amount_debit": 0.0, "amount_sell_card": 0.0, "amount_credit": 0.0, "amount_collection": 0.0,
            "user_id_start": None, "user_id_end": None, "comment": None
        }]
        result = self.client.get_cash_shifts(date_from="2025-10-12")

        self.assertEqual(result, expected)
    
    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_cash_shifts_empty(self, mock_make_request):
        mock_make_request.return_value = {"response": []}
        self.assertEqual(self.client.get_cash_shifts(), [])

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_transactions_params_and_passthrough(self, mock_make_request):
        mock_response_data = [{"transaction_id": 1, "sum": 150}]
        mock_make_request.return_value = {"response": mock_response_data}

        result = self.client.get_transactions(
            date_from="2025-10-12", date_to="2025-10-13", spot_id=1, 
            include_products=True, include_delivery=True
        )

        self.assertEqual(result, mock_response_data)
        mock_make_request.assert_called_once_with(
            "GET", "dash.getTransactions",
            params={
                "dateFrom": "20251012", "dateTo": "20251013", "status": 2,
                "include_products": "true", "include_delivery": "true", "type": "spots", "id": 1
            }
        )

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_transactions_products_params(self, mock_make_request):
        mock_response_data = [{"product_id": 10, "count": 2}]
        mock_make_request.return_value = {"response": mock_response_data}

        result = self.client.get_transactions_products(transaction_ids=[101, 102, 103])

        self.assertEqual(result, mock_response_data)
        mock_make_request.assert_called_once_with(
            "GET", "dash.getTransactionsProducts",
            params={"transactions_id": "101,102,103"}
        )

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_payments_id_success(self, mock_make_request):
        mock_make_request.return_value = {"response": [
            {"payment_method_id": 1, "title": "Наличные"}, {"payment_method_id": 2, "title": "Карта"}
        ]}
        expected = [
            {"payment_method_id": 1, "title": "Наличные"}, {"payment_method_id": 2, "title": "Карта"}
        ]
        self.assertEqual(self.client.get_payments_id(), expected)

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_workshop_success(self, mock_make_request):
        mock_make_request.return_value = {"response": [
            {"workshop_id": 2, "workshop_name": "Кухня", "delete": 0}
        ]}
        expected = [{"workshop_id": 2, "workshop_name": "Кухня", "delete": 0}]
        self.assertEqual(self.client.get_workshop(), expected)

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_get_spots_success(self, mock_make_request):
        mock_make_request.return_value = {"response": [
            {"spot_id": 1, "name": "Кафе", "address": ""}
        ]}
        expected = [{"spot_id": 1, "spot_name": "Кафе", "spot_address": ""}]
        self.assertEqual(self.client.get_spots(), expected)    

if __name__ == '__main__':
    unittest.main()
    
    
    
    
    
    
SHIFT_START_DT = datetime(2025, 10, 13, 10, 0, 0)
SHIFT_END_DT = datetime(2025, 10, 13, 20, 0, 0)

REGULAR_TX_DT = datetime(2025, 10, 13, 12, 30, 0)
DELIVERY_TX_DT = datetime(2025, 10, 13, 15, 0, 0)


class TestComplexLogic(unittest.TestCase):

    def setUp(self):
        self.client = PosterAPIClient(api_token="fake_token", api_url="fake_url")
        self.test_date = "2025-10-13"

    @patch('poster_api.client.PosterAPIClient.get_transactions')
    @patch('poster_api.client.PosterAPIClient.get_cash_shifts')
    def test_get_sales_no_shifts_found(self, mock_get_shifts, mock_get_transactions):
        mock_get_shifts.return_value = []
        
        result = self.client.get_sales_by_shift_with_delivery(date=self.test_date)
        
        self.assertEqual(result, {})
        mock_get_transactions.assert_not_called()

    @patch('poster_api.client.PosterAPIClient.get_transactions')
    @patch('poster_api.client.PosterAPIClient.get_cash_shifts')
    def test_get_sales_no_transactions_found(self, mock_get_shifts, mock_get_transactions):
        mock_get_shifts.return_value = [{
            'poster_shift_id': 101,
            'date_start': SHIFT_START_DT.strftime("%Y-%m-%d %H:%M:%S"),
            'date_end': SHIFT_END_DT.strftime("%Y-%m-%d %H:%M:%S"),
            'amount_sell_cash': 150.00, 
            'amount_sell_card': 250.00,
        }]
        mock_get_transactions.return_value = []

        result = self.client.get_sales_by_shift_with_delivery(date=self.test_date)

        self.assertEqual(result, {})

    @patch('poster_api.client.asyncio.run')
    @patch('poster_api.client.PosterAPIClient.get_transactions_products')
    @patch('poster_api.client.PosterAPIClient.get_transactions')
    @patch('poster_api.client.PosterAPIClient.get_cash_shifts')
    def test_get_sales_full_scenario_with_tips_and_distribution(
        self, mock_get_shifts, mock_get_transactions, mock_get_tx_products, mock_asyncio_run
    ):
        """Тест: полный сценарий с распределением продаж и чаевых по смене."""
        mock_get_shifts.return_value = [{
            'poster_shift_id': 101,
            'date_start': SHIFT_START_DT.strftime("%Y-%m-%d %H:%M:%S"),
            'date_end': SHIFT_END_DT.strftime("%Y-%m-%d %H:%M:%S"),
            'amount_sell_cash': 100.00, 
            'amount_sell_card': 150.00,
        }]

        # Мокаем транзакции
        mock_get_transactions.return_value = [
            {'transaction_id': '1'}, # Обычная продажа
            {'transaction_id': '2'}  # Доставка Glovo
        ]

        # Мокаем продукты в этих транзакциях
        mock_get_tx_products.return_value = [
            {
                'transaction_id': '1', 'product_id': 600, 'product_name': 'Chicken Soup',
                'num': 1.0, 'payed_sum': 80.00, 'product_profit': 4000,
                'time': int(REGULAR_TX_DT.timestamp() * 1000) 
            },
            {
                'transaction_id': '2', 'product_id': 20, 'product_name': 'Pizza',
                'num': 1.0, 'payed_sum': 165.00, 'product_profit': 7000,
                'time': int(DELIVERY_TX_DT.timestamp() * 1000) 
            }
        ]
        
        # Мокаем вызов истории для получения типа оплаты и чаевых
        mock_asyncio_run.return_value = [
            # tx_id, actions, payment_method_id, tip_sum
            ('1', [], 2, 0.0),       # Обычная оплата картой (id=2), без чаевых
            ('2', [], 12, 15.50),    # Оплата Glovo CARD (id=12), чаевые 15.50
        ]
        
        result = self.client.get_sales_by_shift_with_delivery(date=self.test_date)
        
        self.assertIn(101, result)
        shift_result = result[101]

        self.assertEqual(len(shift_result['regular']), 1)
        self.assertEqual(shift_result['regular'][0]['product_name'], 'Chicken Soup')
        self.assertEqual(shift_result['regular'][0]['payed_sum'], 80.00)
        self.assertEqual(shift_result['regular'][0]['profit'], 40.00) # 4000/100

        self.assertEqual(len(shift_result['delivery']), 1)
        self.assertEqual(shift_result['delivery'][0]['product_name'], 'Pizza')
        self.assertEqual(shift_result['delivery'][0]['payed_sum'], 165.00)
        self.assertEqual(shift_result['delivery'][0]['delivery_service'], 'Glovo CARD')

        self.assertEqual(shift_result['tips'], 15.50)
        self.assertEqual(shift_result['tips_by_service']['Glovo CARD'], 15.50)
        self.assertEqual(shift_result['delivery'][0]['tips'], 15.50)

        
        # Сумма по транзакциям = 80.00 (капучино) + 165.00 (пицца) = 245.00
        # Разница = 250.00 - 245.00 = 5.00
        self.assertEqual(shift_result['difference'], 5.00)    
        
        
        


class TestAsyncMethods(TestCase):
    def setUp(self):
        self.client = PosterAPIClient(api_token="fake_token", api_url="fake_url")

    def test_fetch_all_histories_empty_input(self):
        async def run_test():
            result = await self.client.fetch_all_histories([])
            self.assertEqual(result, [])
        
        asyncio.run(run_test())

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_fetch_all_histories_success(self, mock_make_request):
        def request_side_effect(method, endpoint, params):
            tx_id = params.get("transaction_id")
            if tx_id == '101':
                return {"response": [{"type_history": "close", "value_text": '{"payment_method_id": "2", "tip_sum": "10.5"}'}]}
            if tx_id == '102':
                return {"response": [{"type_history": "close", "value_text": '{"payment_method_id": "12"}'}]}
            return {"response": []}

        mock_make_request.side_effect = request_side_effect

        async def run_test():
            transaction_ids = ['101', '102']
            results = await self.client.fetch_all_histories(transaction_ids)
            self.assertEqual(len(results), 2)
            results_dict = {res[0]: res for res in results}
            self.assertEqual(results_dict['101'][2], 2)
            self.assertEqual(results_dict['101'][3], 10.5)
            self.assertEqual(results_dict['102'][2], 12)
            self.assertEqual(results_dict['102'][3], 0.0)
            self.assertEqual(mock_make_request.call_count, 2)

        asyncio.run(run_test())

    @patch('poster_api.client.PosterAPIClient.make_request')
    def test_fetch_all_histories_partial_failure(self, mock_make_request):
        def request_side_effect(method, endpoint, params):
            tx_id = params.get("transaction_id")
            if tx_id == '101':
                return {"response": [{"type_history": "close", "value_text": '{"payment_method_id": "2"}'}]}
            if tx_id == 'FAIL':
                raise Exception("API call failed")
            return {"response": []}

        mock_make_request.side_effect = request_side_effect
        
        async def run_test():
            transaction_ids = ['101', 'FAIL']
            results = await self.client.fetch_all_histories(transaction_ids)
            self.assertEqual(len(results), 2)
            results_dict = {res[0]: res for res in results}
            self.assertEqual(results_dict['101'][2], 2)
            failed_result = results_dict['FAIL']
            self.assertEqual(failed_result[0], 'FAIL')
            self.assertEqual(failed_result[1], [])
            self.assertIsNone(failed_result[2])
        
        asyncio.run(run_test())
        
        

class PosterUtilsTestCase(TestCase):
    def test_parse_poster_datetime(self):
        self.assertIsNone(parse_poster_datetime(None))

        dt = parse_poster_datetime(1672531200)  # 2023-01-01 00:00:00 UTC
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertTrue(timezone.is_aware(dt))

        dt = parse_poster_datetime(1672531200000)
        self.assertEqual(dt.year, 2023)

        dt = parse_poster_datetime("2023-01-01 12:30:00")
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 30)
        self.assertTrue(timezone.is_aware(dt))
        
        self.assertIsNone(parse_poster_datetime("not-a-date"))


class PosterSavingServiceTestCase(TestCase):
    def setUp(self):
        self.api_client = MagicMock()

    def test_save_shift_sales_to_db(self):
        date_str = "2023-10-10"
        
        mock_response = {
            "123": {
                "regular": [
                    {"payed_sum": "100.00", "profit": "50.00", "product_name": "Burger", "count": 1, "category": "Food"}
                ],
                "delivery": [],
                "tips": "10.00"
            }
        }
        self.api_client.get_sales_by_shift_with_delivery.return_value = mock_response

        save_shift_sales_to_db(self.api_client, date_str)

        shift = ShiftSale.objects.get(shift_id=123)
        self.assertEqual(shift.total_revenue, Decimal("100.00"))
        self.assertEqual(shift.total_profit, Decimal("50.00"))
        self.assertEqual(shift.tips, Decimal("10.00"))
        
        item = ShiftSaleItem.objects.get(shift_sale=shift)
        self.assertEqual(item.product_name, "Burger")
        self.assertEqual(item.profit, Decimal("50.00"))

        mock_response["123"]["regular"][0]["payed_sum"] = "200.00" 
        save_shift_sales_to_db(self.api_client, date_str)
        
        shift.refresh_from_db()
        self.assertEqual(shift.total_revenue, Decimal("200.00"))

    def test_save_cash_shifts_range(self):
        mock_response = [
            {
                "poster_shift_id": 555,
                "date_start": "2023-10-10 08:00:00",
                "date_end": "2023-10-10 20:00:00",
                "amount_sell_cash": "500",
                "amount_sell_card": "1000",
                "comment": "Good day"
            }
        ]
        self.api_client.get_cash_shifts.return_value = mock_response

        save_cash_shifts_range(self.api_client, "2023-10-10")

        shift = CashShiftReport.objects.get(poster_shift_id=555)
        self.assertEqual(shift.total_sales, Decimal("1500"))
        self.assertEqual(shift.comment, "Good day")

    def test_save_products_and_categories(self):
        cat_data = [{"category_id": 10, "category_name": "Drinks"}]
        save_categories(cat_data)
        self.assertTrue(Category.objects.filter(category_id=10).exists())

        prod_data = [
            {"product_id": 100, "product_name": "Cola", "category_id": 10, "category_name": "Drinks", "cost": "20.50"}
        ]
        save_products(prod_data)
        
        product = Product.objects.get(product_id=100)
        self.assertEqual(product.product_name, "Cola")
        self.assertEqual(product.category.category_id, 10)
        self.assertEqual(product.cost, Decimal("20.50"))

        prod_data[0]["product_name"] = "Pepsi"
        save_products(prod_data)
        product.refresh_from_db()
        self.assertEqual(product.product_name, "Pepsi")

    @unittest.skip
    def test_save_products_sales(self):
        data = [{
            "product_id": 1, 
            "product_name": "Pizza", 
            "category_id": 20, 
            "category_name": "Food",
            "count": 5,
            "product_profit": "150.00"
        }]
        
        save_products_sales(data)
        
        sale = ProductSales.objects.get(product_id=1)
        self.assertEqual(sale.count, 5)
        self.assertEqual(sale.product_profit, Decimal("150.00"))
        self.assertTrue(Product.objects.filter(product_id=1).exists())

    def test_save_categories_sales(self):
        data = [{
            "category_id": 30,
            "category_name": "Beer",
            "profit": "500.00",
            "count": 10
        }]
        save_categories_sales(data)
        
        sale = CategoriesSales.objects.get(category__category_id=30)
        self.assertEqual(sale.profit, Decimal("500.00"))

    def test_save_transactions_full_flow(self):
        """
        """
        tx_data = [{
            "transaction_id": 999,
            "date_start": "2023-11-01 12:00:00",
            "date_close": "2023-11-01 12:30:00",
            "payed_sum": "1200",
            "sum": "1200",
            "total_profit": "500",
            "comment": "",
            "reason": "",
            "spot_id": 1,
            "status": 2,
            "pay_type": 1,
            "service_mode": 1,
            "processing_status": 10,
            "client": {
                "id": 777, 
                "firstname": "John", 
                "lastname": "Doe", 
                "name": "John Doe", 
                "phone": "+1234567890",
                "email": "john@example.com"}
        }]
        
        save_transactions(tx_data)
        
        tx = Transactions.objects.get(transaction_id=999)
        self.assertEqual(tx.client_id, "777")
        self.assertEqual(tx.client_firstname, "John")

        Category.objects.create(category_id=1, category_name="Test")
        Product.objects.create(product_id=50, product_name="Steak", category_id=1)

        tx_prod_data = [{
            "transaction_id": 999,
            "product_id": 50,
            "num": 2,
            "payed_sum": "1200",
            "client": {
                "id": 777, 
                "firstname": "John", 
                "lastname": "Doe", 
                "name": "John Doe", 
                "phone": "+1234567890",
                "email": "john@example.com"}
        }]

        save_transactions_products(tx_prod_data)

        link = TransactionsProducts.objects.get(transaction__transaction_id=999, product__product_id=50)
        self.assertEqual(link.num, 2.0)
        
        client = Clients.objects.get(client_id=777)
        self.assertEqual(client.firstname, "John")
        
    def test_save_transaction_history(self):
        tx = Transactions.objects.create(
            transaction_id=888, 
            date_start=timezone.now(),
            date_close=timezone.now()
        )
        
        history_data = [{
            "type_history": "open",
            "time": "2023-11-01 10:00:00",
            "value": 1
        }]
        
        save_transaction_history(888, history_data)
        
        h_obj = TransactionHistory.objects.get(transaction=tx)
        self.assertEqual(h_obj.type_history, "open")

    def test_static_data_savers(self):
        save_workshop([{"workshop_id": 1, "workshop_name": "Kitchen"}])
        self.assertTrue(Workshop.objects.filter(workshop_id=1).exists())

        save_payments_id([{"payment_method_id": 2, "title": "Cash"}])
        self.assertTrue(Payments_ID.objects.filter(payment_method_id=2).exists())

        save_clients([{"client_id": 10, "firstname": "Alice", "name": "Alice Wonder"}])
        self.assertTrue(Clients.objects.filter(client_id=10).exists())
        
        create_role_lists(None)
        self.assertTrue(Role.objects.filter(name='Официант').exists())

    @patch("poster_api.services.saving.save_workshop")
    @patch("poster_api.services.saving.save_payments_id")
    @patch("poster_api.services.saving.save_products")
    @patch("poster_api.services.saving.save_categories")
    @patch("poster_api.services.saving.save_cash_shifts_range")
    @patch("poster_api.services.saving.save_shift_sales_to_db")
    def test_sync_all_from_date(self, mock_shifts, mock_cash, mock_cat, mock_prod, mock_pay, mock_work):
        self.api_client.get_transactions.return_value = [] 
        
        today_str = date.today().strftime("%Y-%m-%d")
        
        sync_all_from_date(self.api_client, today_str)
        
        mock_work.assert_called_once()
        mock_pay.assert_called_once()
        mock_prod.assert_called_once()
        mock_cat.assert_called_once()
        mock_cash.assert_called_once()
        
        self.assertTrue(mock_shifts.call_count >= 1)
        
        


class PosterApiViewsTest(APITestCase):
    """Tests for Poster API ViewSets using reverse() to match urls.py."""

    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(category_id=1, category_name="Test Cat")
        self.workshop = Workshop.objects.create(workshop_id=10, workshop_name="Kitchen")
        self.product = Product.objects.create(
            product_id=100, 
            product_name="Burger", 
            workshop=10, 
            category=self.category,
            cost=500
        )
        self.spot = Spot.objects.create(spot_id=1, spot_name="Main Spot", spot_address="Street 1")
        self.shift_sale = ShiftSale.objects.create(shift_id=12345, date=date(2025, 10, 1))

        self.url_cash_shifts = reverse('cash_shift-list')
        self.url_shift_sales = reverse('shift_sales-list')
        self.url_transactions = reverse('transactions-list')
        self.url_payment_methods = reverse('payment_methods-list')
        self.url_workshops = reverse('workshop-list')
        self.url_products = reverse('products-list')
        self.url_spots = reverse('spots-list')

    @patch('poster_api.views.PosterAPIClient')
    def test_cash_shifts_list_success(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_cash_shifts.return_value = [{
            "poster_shift_id": 1,
            "date_start": "2025-10-01 10:00:00",
            "date_end": "2025-10-01 22:00:00",
            "amount_sell_cash": 1000.0,
            "amount_sell_card": 500.0,
            "amount_start": 100.0,
            "amount_end": 100.0,
            "amount_debit": 0,
            "amount_credit": 0,
            "amount_collection": 0,
            "comment": "Test",
            "user_id_start": 1,
            "user_id_end": 1
        }]

        response = self.client.get(self.url_cash_shifts, {'dateFrom': '2025-10-01', 'dateTo': '2025-10-01'})
        
        if response.status_code == 400:
            print(f"\nCashShift Error: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]['poster_shift_id']), '1')
    
    @patch('poster_api.views.PosterAPIClient')
    def test_cash_shifts_list_error(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_cash_shifts.side_effect = Exception("API Error")

        response = self.client.get(self.url_cash_shifts)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "API Error")

    @patch('poster_api.views.PosterAPIClient')
    def test_shift_sales_list_success(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_sales_by_shift_with_delivery.return_value = {
            "12345": {
                "regular": [{"product_name": "Burger", "payed_sum": 500}],
                "delivery": [],
                "difference": 0,
                "tips": 50
            }
        }

        response = self.client.get(self.url_shift_sales, {'date': '2025-10-01', 'spot_id': ['1']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data[0]
        
        self.assertEqual(float(data['tips']), 50.0)
        self.assertEqual(len(data['regular']), 1)
        self.assertEqual(data['regular'][0]['product_name'], "Burger")

    @patch('poster_api.views.PosterAPIClient')
    def test_shift_sales_list_invalid_spot_id(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_sales_by_shift_with_delivery.return_value = {}

        response = self.client.get(self.url_shift_sales, {'spot_id': ['abc']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @patch('poster_api.views.PosterAPIClient')
    def test_shift_sales_list_api_error(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_sales_by_shift_with_delivery.side_effect = Exception("Connection Fail")

        response = self.client.get(self.url_shift_sales)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @patch('poster_api.views.PosterAPIClient')
    def test_transactions_history_success(self, MockClient):
        mock_instance = MockClient.return_value
        
        mock_transaction_obj = MagicMock()
        mock_transaction_obj.pk = 999
        
        async_mock = AsyncMock(return_value=[{
            "transaction_id": 999,
            "transaction": mock_transaction_obj,
            "sum": 1000,
            "type_history": "open", 
            "time": "2025-10-01 10:00:00",
            "history": [],
            "date_start": "2025-10-01 10:00:00",
            "date_close": "2025-10-01 10:05:00",
            "status": 2,
            "pay_type": 1,
            "spot_id": 1
        }])
        mock_instance.get_full_transactions_for_day = async_mock

        response = self.client.get(self.url_transactions, {
            'date_from': '2025-10-01', 
            'date_to': '2025-10-02'
        })
        
        if response.status_code == 500:
            print(f"\nTX Error: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_transactions_history_missing_params(self):
        response = self.client.get(self.url_transactions)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('poster_api.views.PosterAPIClient')
    def test_transactions_history_exception(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_full_transactions_for_day = AsyncMock(side_effect=Exception("Async Error"))

        response = self.client.get(self.url_transactions, {
            'date_from': '2025-10-01', 
            'date_to': '2025-10-02'
        })
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('poster_api.views.PosterAPIClient')
    def test_payment_methods_list(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_payments_id.return_value = [{"payment_method_id": 1, "title": "Cash"}]

        response = self.client.get(self.url_payment_methods)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Cash")

    def test_workshop_list(self):
        response = self.client.get(self.url_workshops)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        data = response.data[0]
        self.assertEqual(data['id'], 10) 
        name = data.get('workshop_name') or data.get('name')
        self.assertEqual(name, "Kitchen")

    def test_product_list(self):
        response = self.client.get(self.url_products)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        data = response.data[0]
        self.assertEqual(data['id'], 100)
        name = data.get('product_name') or data.get('name')
        self.assertEqual(name, "Burger")

    def test_spot_list(self):
        response = self.client.get(self.url_spots)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        data = response.data[0]
        self.assertEqual(data['spot_name'], "Main Spot")