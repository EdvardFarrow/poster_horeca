from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Role
from .serializers import UserSerializer

class UserModelTest(TestCase):
    """
    Tests for the custom User model.
    """

    def setUp(self):
        self.role_manager = Role.objects.create(name='manager')
        self.role_employee = Role.objects.create(name='employee')

    def test_create_user_with_role(self):
        """
        Ensures a user can be created.
        User.role is stored as a string (based on previous errors).
        """
        user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            role='manager' 
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpassword123'))
        self.assertEqual(user.role, 'manager')

    def test_create_superuser(self):
        """
        Ensures a superuser can be created correctly.
        """
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword123'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class UserSerializerTest(TestCase):
    """
    Tests for the UserSerializer.
    """

    def setUp(self):
        self.role = Role.objects.create(name='manager')
        self.user = User.objects.create_user(
            username='serializertest',
            fullname='Serializer Test User',
            password='testpassword',
            role='manager'
        )

    def test_user_serialization(self):
        """
        Ensures user data is correctly serialized.
        """
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'serializertest')
        self.assertEqual(data['fullname'], 'Serializer Test User')
        self.assertEqual(data['role'], 'manager')


class UserViewSetTest(APITestCase):
    """
    Tests for the UserViewSet (CRUD operations via API).
    """

    def setUp(self):
        self.role_manager = Role.objects.create(name='manager')
        self.role_employee = Role.objects.create(name='employee')

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.client.force_authenticate(user=self.admin_user)

        self.user1 = User.objects.create_user(
            username='user1',
            fullname='User One',
            password='user1pass',
            role='employee' 
        )
        
        self.list_url = reverse('user-list') 
        self.detail_url = reverse('user-detail', args=[self.user1.id])

    def test_list_users(self):
        """
        Ensures an authenticated admin can list all users.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_user(self):
        """
        Ensures a single user can be retrieved by ID.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')

    def test_create_user_via_viewset(self):
        """
        Ensures a new user can be created via POST request.
        """
        data = {
            'username': 'new_api_user',
            'password': 'securepass123',
            'fullname': 'API Creator',
            'role': 'employee'
        }
        response = self.client.post(self.list_url, data, format='json')
        
        if response.status_code == 400:
            print(f"\nCreate Error: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        
        new_user = User.objects.get(username='new_api_user')
        self.assertEqual(new_user.role, 'employee')

    def test_update_user(self):
        """
        Ensures a user can be updated via PATCH request.
        """
        data = {
            'fullname': 'Updated Name', 
            'role': 'manager'
        }
        response = self.client.patch(self.detail_url, data, format='json')
        
        if response.status_code == 400:
            print(f"\nUpdate Error: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.fullname, 'Updated Name')
        self.assertEqual(self.user1.role, 'manager')

    def test_delete_user(self):
        """
        Ensures a user can be deleted via DELETE request.
        """
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user1.id).exists())


class MeViewTest(APITestCase):
    """
    Tests for the 'Me' endpoint (current user profile).
    """

    def setUp(self):
        self.role = Role.objects.create(name='employee')
        self.user = User.objects.create_user(
            username='myself',
            password='mypassword',
            role='employee'
        )
        try:
            self.url = reverse('user')
        except:
            self.url = None

    def test_get_me_authenticated(self):
        """
        Ensures authenticated users can retrieve their own data.
        """
        if not self.url:
            self.fail("Could not resolve URL for 'user'. Check urls.py names.")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'myself')

    def test_get_me_unauthenticated(self):
        """
        Ensures unauthenticated requests are rejected.
        """
        if not self.url:
            self.fail("Could not resolve URL for 'user'.")
            
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)