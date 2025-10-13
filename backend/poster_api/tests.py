import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import requests
from django.test import TestCase
import asyncio
from .client import PosterAPIClient 

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
    
    
    
    
    
    
# Предварительно подготовленные данные для тестов
# Время для смены: с 10:00 до 20:00
SHIFT_START_DT = datetime(2025, 10, 13, 10, 0, 0)
SHIFT_END_DT = datetime(2025, 10, 13, 20, 0, 0)

# Время для транзакций внутри смены
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
        # Мокаем кассовую смену
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

    # Метод стал СИНХРОННЫМ
    def test_fetch_all_histories_empty_input(self):
        # Асинхронный код запускается через asyncio.run()
        async def run_test():
            result = await self.client.fetch_all_histories([])
            self.assertEqual(result, [])
        
        asyncio.run(run_test())

    @patch('poster_api.client.PosterAPIClient.make_request')
    # Метод стал СИНХРОННЫМ
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
    # Метод стал СИНХРОННЫМ
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