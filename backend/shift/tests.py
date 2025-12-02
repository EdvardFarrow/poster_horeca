from datetime import date
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import Employee, Role
from poster_api.models import ShiftSale
from salary.models import SalaryRecord 
from .models import Shift, ShiftEmployee
from users.models import User

class ShiftModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='waiter')
        self.employee = Employee.objects.create(name='John Doe', role=self.role)
        self.shift = Shift.objects.create(date=date(2025, 10, 1), shift_id=100)

    def test_shift_str(self):
        """Tests the string representation of the Shift model."""
        self.assertIn("2025-10-01", str(self.shift))
        self.assertIn("100", str(self.shift))

    def test_shift_employee_str(self):
        """Tests the string representation of the ShiftEmployee model."""
        shift_emp = ShiftEmployee.objects.create(
            shift=self.shift,
            employee=self.employee,
            role=self.role
        )
        self.assertIn("John Doe", str(shift_emp))
        self.assertIn("waiter", str(shift_emp))


class ShiftViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.force_authenticate(user=self.user)

        self.role_waiter = Role.objects.create(name='waiter')
        self.role_chef = Role.objects.create(name='chef')
        self.emp1 = Employee.objects.create(name='Alice', role=self.role_waiter)
        self.emp2 = Employee.objects.create(name='Bob', role=self.role_chef)
        self.list_url = reverse('shift-list') 
        self.save_month_url = reverse('shift-save-month')

    def test_list_shifts_success(self):
        """Ensures list endpoint returns simplified calendar structure."""
        s1 = Shift.objects.create(date=date(2025, 10, 1))
        ShiftEmployee.objects.create(shift=s1, employee=self.emp1, role=self.emp1.role)
        s2 = Shift.objects.create(date=date(2025, 10, 2))
        ShiftEmployee.objects.create(shift=s2, employee=self.emp1, role=self.emp1.role)
        ShiftEmployee.objects.create(shift=s2, employee=self.emp2, role=self.emp2.role)
        Shift.objects.create(date=date(2025, 11, 1))

        response = self.client.get(self.list_url, {'month': 10, 'year': 2025})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        shift_2 = next(item for item in data if item['date'] == '2025-10-02')
        self.assertIn(self.emp1.id, shift_2['employees'])
        self.assertIn(self.emp2.id, shift_2['employees'])

    def test_save_month_validation_error(self):
        """Ensures 400 error if month or year are missing."""
        payload = {"shifts": []}
        response = self.client.post(self.save_month_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_month_creates_new_shifts(self):
        """Ensures valid payload creates new shifts."""
        payload = {
            "month": 10,
            "year": 2025,
            "shifts": [
                {
                    "date": "2025-10-05",
                    "employees": [self.emp1.id]
                }
            ]
        }
        response = self.client.post(self.save_month_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Shift.objects.filter(date=date(2025, 10, 5)).exists())
        shift = Shift.objects.get(date=date(2025, 10, 5))
        self.assertEqual(shift.employees.count(), 1)
        self.assertEqual(shift.employees.first(), self.emp1)

    def test_save_month_overwrites_existing(self):
        """Ensures old shifts are deleted before creating new ones."""
        old_shift = Shift.objects.create(date=date(2025, 10, 1))
        try:
            SalaryRecord.objects.create(shift=old_shift, employee=self.emp1, amount=100)
        except:
            pass
            
        payload = {
            "month": 10,
            "year": 2025,
            "shifts": [
                {
                    "date": "2025-10-15",
                    "employees": [self.emp2.id]
                }
            ]
        }
        response = self.client.post(self.save_month_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(Shift.objects.filter(date=date(2025, 10, 1)).exists())
        self.assertTrue(Shift.objects.filter(date=date(2025, 10, 15)).exists())

    def test_save_month_links_poster_shift(self):
        """Ensures new shift links to existing Poster shift if available."""
        ShiftSale.objects.create(date=date(2025, 10, 20), shift_id=9999)
        payload = {
            "month": 10,
            "year": 2025,
            "shifts": [
                {
                    "date": "2025-10-20",
                    "employees": [self.emp1.id]
                }
            ]
        }
        self.client.post(self.save_month_url, payload, format='json')
        created_shift = Shift.objects.get(date=date(2025, 10, 20))
        self.assertEqual(created_shift.shift_id, 9999)

    def test_save_month_ignores_invalid_employee(self):
        """Ensures non-existent employee IDs are ignored."""
        payload = {
            "month": 10,
            "year": 2025,
            "shifts": [
                {
                    "date": "2025-10-05",
                    "employees": [99999]
                }
            ]
        }
        response = self.client.post(self.save_month_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        shift = Shift.objects.get(date=date(2025, 10, 5))
        self.assertEqual(shift.employees.count(), 0)

    def test_save_month_ignores_bad_date_format(self):
        """Ensures invalid date formats are ignored."""
        payload = {
            "month": 10,
            "year": 2025,
            "shifts": [
                {
                    "date": "invalid-date-format", 
                    "employees": [self.emp1.id]
                }
            ]
        }
        response = self.client.post(self.save_month_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Shift.objects.count(), 0)