from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import PlannedShift

User = get_user_model()

class PlannedShiftTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager_test', 
            password='testpassword', 
            role='manager'
        )
        
        self.client.force_authenticate(user=self.manager)

        self.base_url = reverse('planned-shift-list') 
        
        self.test_date = date(2025, 8, 25) 
        self.other_date = date(2025, 8, 26) 
        
        self.shift_data = {
            'user_id': self.manager.id,
            'date': self.test_date.isoformat(),
            'role': 'Chef',
            'planned_start_time': '09:00:00',
            'planned_end_time': '17:00:00',
        }
        PlannedShift.objects.create(
            user=self.manager,
            date=self.test_date,
            role='Waiter',
            planned_start_time='10:00:00',
            planned_end_time='22:00:00',
            created_by=self.manager
        )
        
        PlannedShift.objects.create(
            user=self.manager,
            date=self.other_date,
            role='Barman',
            planned_start_time='18:00:00',
            planned_end_time='02:00:00',
            created_by=self.manager
        )



class PlannedShiftCRDTests(PlannedShiftTests):
    
    def test_create_planned_shift(self):
        """Проверяет успешное создание новой запланированной смены."""
        new_data = self.shift_data.copy()
        new_data['date'] = '2025-09-01' 
        response = self.client.post(self.base_url, new_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlannedShift.objects.count(), 3)
        self.assertEqual(response.data['role'], 'Chef')
        self.assertEqual(response.data['created_by']['id'], self.manager.id)

    def test_list_planned_shifts(self):
        """Проверяет получение списка всех запланированных смен."""
        response = self.client.get(self.base_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 

    def test_retrieve_single_planned_shift(self):
        """Проверяет получение одной запланированной смены по ID."""
        shift = PlannedShift.objects.get(date=self.test_date)
        url = reverse('planned-shift-detail', kwargs={'pk': shift.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'Waiter')



class PlannedShiftActionTests(PlannedShiftTests):
    
    def test_filter_by_date(self):
        """Проверяет фильтрацию по полю 'date'."""
        response = self.client.get(self.base_url, {'date': self.test_date.isoformat()})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['date'], self.test_date.isoformat())

    def test_filter_by_user(self):
        """Проверяет фильтрацию по полю 'user'."""
        response = self.client.get(self.base_url, {'user': self.manager.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 

    def test_by_week_action_success(self):
        """Проверяет экшен by_week с корректным диапазоном."""
        url = reverse('planned-shift-by-week')
        start = '2025-08-25'
        end = '2025-08-31' 
        response = self.client.get(url, {'start': start, 'end': end})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 

    def test_by_month_action_success(self):
        """Проверяет экшен by_month с корректным месяцем."""
        url = reverse('planned-shift-by-month')
        response = self.client.get(url, {'year': 2025, 'month': 8})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)