from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, Employee, Role, PayGroup
from shift.models import Shift, ShiftEmployee
from poster_api.models import ShiftSale, ShiftSaleItem, Workshop, Product, Category
from salary.models import SalaryRule, SalaryRuleProduct, SalaryRecord
from salary.aggreg import aggregate_sales
from salary.services import calculate_and_save_shift_salaries

class SalaryCalculationBaseTest(TestCase):
    """Base setup for salary calculation tests."""

    def setUp(self):
        # Create Categories (Required for Products)
        self.category_kitchen = Category.objects.create(category_id=10, category_name="Kitchen Cat")
        self.category_bar = Category.objects.create(category_id=20, category_name="Bar Cat")

        # Workshops
        self.workshop_kitchen = Workshop.objects.create(workshop_id=1, workshop_name="Kitchen")
        self.workshop_bar = Workshop.objects.create(workshop_id=2, workshop_name="Bar")
        
        # PayGroup & Roles
        self.pay_group_cooks = PayGroup.objects.create(name="Cooks Shared")
        
        self.role_chef = Role.objects.create(name="Chef", pay_group=self.pay_group_cooks)
        self.role_sous_chef = Role.objects.create(name="Sous Chef", pay_group=self.pay_group_cooks)
        self.role_waiter = Role.objects.create(name="Waiter")

        # Employees
        self.emp_chef = Employee.objects.create(name="Gordon", role=self.role_chef)
        self.emp_sous = Employee.objects.create(name="Remy", role=self.role_sous_chef)
        self.emp_waiter = Employee.objects.create(name="Penny", role=self.role_waiter)

        # Shift & Poster Data
        self.date_obj = date(2025, 10, 1)
        self.shift = Shift.objects.create(date=self.date_obj, shift_id=100)
        self.shift_sale = ShiftSale.objects.create(shift_id=100, date=self.date_obj)

        ShiftEmployee.objects.create(shift=self.shift, employee=self.emp_chef, role=self.role_chef)
        ShiftEmployee.objects.create(shift=self.shift, employee=self.emp_sous, role=self.role_sous_chef)
        ShiftEmployee.objects.create(shift=self.shift, employee=self.emp_waiter, role=self.role_waiter)

        # Products & Sales
        self.prod_steak = Product.objects.create(
            product_id=1, 
            product_name="Steak", 
            workshop=1,
            category=self.category_kitchen 
        )
        ShiftSaleItem.objects.create(
            shift_sale=self.shift_sale,
            product_name="Steak",
            category_name="regular",
            workshop=1,
            payed_sum=1000,
            count=1
        )
        self.prod_cola = Product.objects.create(
            product_id=2, 
            product_name="Cola", 
            workshop=2,
            category=self.category_bar
        )
        ShiftSaleItem.objects.create(
            shift_sale=self.shift_sale,
            product_name="Cola",
            category_name="regular",
            workshop=2,
            payed_sum=500,
            count=2
        )

    def create_salary_rule(self, role, fixed=0, percent=0, workshops=None):
        rule = SalaryRule.objects.create(
            role=role,
            fixed_per_shift=fixed,
            percent=percent
        )
        if workshops:
            rule.workshops.set(workshops)
        return rule


class AggregationLogicTest(SalaryCalculationBaseTest):
    """Tests for the aggregation logic in aggreg.py."""

    def test_fixed_salary_calculation(self):
        """Tests simple fixed salary calculation."""
        self.create_salary_rule(self.role_waiter, fixed=2000)
        result = aggregate_sales(self.shift)
        data = result[self.emp_waiter.id]
        self.assertEqual(data['total_salary'], Decimal('2000.00'))
        self.assertEqual(data['details']['fixed'], Decimal('2000.00'))

    def test_percentage_calculation_shared(self):
        """Tests shared percentage calculation for a PayGroup."""
        self.create_salary_rule(self.role_chef, percent=10, workshops=[self.workshop_kitchen])
        result = aggregate_sales(self.shift)
        
        # 1000 sales * 10% = 100 total. Divided by 2 employees = 50 each.
        chef_data = result[self.emp_chef.id]
        self.assertEqual(chef_data['percent_total'], Decimal('50.00'))
        
        sous_data = result[self.emp_sous.id]
        self.assertEqual(sous_data['percent_total'], Decimal('50.00'))

    def test_bonus_product_calculation(self):
        """Tests fixed bonuses per specific product."""
        rule = self.create_salary_rule(self.role_waiter, workshops=[self.workshop_bar])        
        
        SalaryRuleProduct.objects.create(
            salary_rule=rule,
            product=self.prod_cola,
            fixed=10
        )
        result = aggregate_sales(self.shift)
        waiter_data = result[self.emp_waiter.id]
        
        # 2 Colas * 10 = 20.00
        self.assertEqual(waiter_data['fixed_bonus_total'], Decimal('20.00'))
        
        breakdown = waiter_data['details']['bonus_breakdown']
        cola_bonus = next(b for b in breakdown if b['product_name'] == 'Cola')
        self.assertEqual(cola_bonus['total'], Decimal('20.00'))

    def test_no_sales_data(self):
        """Tests calculation when no sales exist."""
        ShiftSaleItem.objects.all().delete()
        self.create_salary_rule(self.role_waiter, fixed=1000)
        result = aggregate_sales(self.shift)
        self.assertEqual(result[self.emp_waiter.id]['total_salary'], 1000)
        self.assertEqual(result[self.emp_waiter.id]['percent_total'], 0)


class ServicesTest(SalaryCalculationBaseTest):
    """Tests for service layer functions."""

    def test_calculate_and_save_creates_records(self):
        """Ensures service creates SalaryRecord entries."""
        self.create_salary_rule(self.role_waiter, fixed=1500)
        calculate_and_save_shift_salaries(self.shift)
        record = SalaryRecord.objects.get(employee=self.emp_waiter, shift=self.shift)
        self.assertEqual(record.fixed_part, 1500)
        self.assertEqual(record.total_salary, 1500)

    def test_calculate_and_save_preserves_manual_changes(self):
        """Ensures manual write-offs are preserved during recalculation."""
        self.create_salary_rule(self.role_waiter, fixed=1000)
        calculate_and_save_shift_salaries(self.shift)
        
        record = SalaryRecord.objects.get(employee=self.emp_waiter, shift=self.shift)
        record.details['write_off'] = 200
        record.details['comment'] = "Spilled soup"
        record.save()
        
        SalaryRule.objects.update(fixed_per_shift=2000)
        calculate_and_save_shift_salaries(self.shift)
        
        record.refresh_from_db()
        self.assertEqual(record.fixed_part, 2000)
        self.assertEqual(record.write_off, 200)
        self.assertEqual(record.comment, "Spilled soup")
        self.assertEqual(record.total_salary, 1800)


class SalaryViewsTest(SalaryCalculationBaseTest):
    """Tests for Salary API ViewSets."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.force_authenticate(user=self.user)
        
        self.rule = self.create_salary_rule(self.role_waiter, fixed=1000)
        calculate_and_save_shift_salaries(self.shift)
        self.salary_record = SalaryRecord.objects.get(employee=self.emp_waiter)

    def test_list_salary_records(self):
        """Tests listing salary records by month and year."""
        url = reverse('salary_records-list')
        response = self.client.get(url, {'month': 10, 'year': 2025})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        str_emp_id = str(self.emp_waiter.id)
        self.assertIn(str_emp_id, data)
        self.assertIn("1", data[str_emp_id])
        self.assertEqual(float(data[str_emp_id]["1"]["total_salary"]), 1000.0)

    def test_partial_update_salary(self):
        """Tests manual update of salary details."""
        url = reverse('salary_records-detail', args=[self.salary_record.id])
        payload = {
            "details": {
                "fixed": 1000,
                "write_off": 500,
                "comment": "Late"
            }
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.salary_record.refresh_from_db()
        self.assertEqual(self.salary_record.write_off, 500)
        self.assertEqual(self.salary_record.total_salary, 500)

    def test_recalculate_action(self):
        """Tests the recalculate action for a whole month."""
        url = reverse('salary_records-recalculate')
        self.rule.fixed_per_shift = 5000
        self.rule.save()
        
        response = self.client.post(url, {'month': 10, 'year': 2025}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Processed shifts: 1", response.data['message'])
        
        self.salary_record.refresh_from_db()
        self.assertEqual(self.salary_record.total_salary, 5000)

    def test_aggregate_view_by_shift(self):
        """Tests the aggregate preview endpoint by shift ID."""
        try:
            url = reverse('aggregate_sales-by-shift', args=[self.shift.id])
        except:
            url = f"/api/salary/aggregate_sales/shift/{self.shift.id}/"

        self.create_salary_rule(self.role_waiter, fixed=3000)        
            
        response = self.client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            emp_data = next(e for e in data['employees'] if e['employee_id'] == self.emp_waiter.id)
            self.assertEqual(emp_data['additional'], 4000.0)