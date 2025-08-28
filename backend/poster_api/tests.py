from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class PosterAPITests(APITestCase):

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(username="testuser", password="password")
        # Форсируем аутентификацию
        self.client.force_authenticate(user=self.user)
        self.url = reverse('analytics-list')  # viewset list

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_waiters(self, mock_get_analytics):
        mock_get_analytics.return_value = [
            {"employee_id": 1, "employee_name": "John Doe", "orders_count": 5, "sum": 1000, "avg_check": 200}
        ]
        response = self.client.get(self.url, {"type": "waiters"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'waiters')
        self.assertEqual(len(response.data['data']), 1)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_clients(self, mock_get_analytics):
        mock_get_analytics.return_value = [
            {"client_id": 1, "client_name": "Alice", "visits": 3, "sum": 500, "avg_check": 166.67}
        ]
        response = self.client.get(self.url, {"type": "clients"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'clients')
        self.assertEqual(len(response.data['data']), 1)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_products(self, mock_get_analytics):
        mock_get_analytics.return_value = [
            {"product_id": 1, "product_name": "Pizza", "sum": 1200, "count": 3}
        ]
        response = self.client.get(self.url, {"type": "products"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'products')
        self.assertEqual(len(response.data['data']), 1)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_categories(self, mock_get_analytics):
        mock_get_analytics.return_value = [
            {"category_id": 1, "category_name": "Food", "sum": 2500, "count": 5}
        ]
        response = self.client.get(self.url, {"type": "categories"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'categories')
        self.assertEqual(len(response.data['data']), 1)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_departments(self, mock_get_analytics):
        mock_get_analytics.return_value = [
            {"department_id": 1, "department_name": "Bar", "sum": 1500, "orders_count": 4}
        ]
        response = self.client.get(self.url, {"type": "spots"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'spots')
        self.assertEqual(len(response.data['data']), 1)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_all_types(self, mock_get_analytics):
        types_map = ["waiters", "clients", "products", "categories", "spots"]
        for t in types_map:
            mock_get_analytics.return_value = []
            response = self.client.get(self.url, {"type": t})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_with_date_filters(self, mock_get_analytics):
        mock_get_analytics.return_value = []
        response = self.client.get(self.url, {"type": "waiters", "dateFrom": "2025-08-01", "dateTo": "2025-08-31"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_with_entity_id(self, mock_get_analytics):
        mock_get_analytics.return_value = []
        response = self.client.get(self.url, {"type": "waiters", "id": 123})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('poster_api.views.PosterAPIClient.get_analytics')
    def test_list_with_api_error(self, mock_get_analytics):
        mock_get_analytics.side_effect = Exception("API error")
        response = self.client.get(self.url, {"type": "waiters"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
