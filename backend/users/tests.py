from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User
from .serializers import RegisterSerializer, UserSerializer

# --- Model Tests ---
class UserModelTest(TestCase):
    """
    Tests for the custom User model.
    """

    def test_create_user(self):
        """
        Ensures a user can be created with a default role.
        """
        user = User.objects.create_user(
            username='testuser',
            password='testpassword123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpassword123'))
        self.assertEqual(user.role, 'manager')  
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_with_role(self):
        """
        Ensures a user can be created with a specified role.
        """
        owner = User.objects.create_user(
            username='owneruser',
            password='ownerpassword123',
            role='owner'
        )
        self.assertEqual(owner.role, 'owner')

        employee = User.objects.create_user(
            username='employeeuser',
            password='employeepassword123',
            role='employee'
        )
        self.assertEqual(employee.role, 'employee')

    def test_create_superuser(self):
        """
        Ensures a superuser can be created.
        """
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword123'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, 'manager') 

    def test_user_str_method(self):
        """
        Tests the __str__ method of the User model.
        """
        user = User.objects.create_user(username='john_doe', password='password123')
        self.assertEqual(str(user), 'john_doe')

# --- Serializer Tests ---
class RegisterSerializerTest(TestCase):
    """
    Tests for the RegisterSerializer.
    """

    def test_valid_registration(self):
        """
        Ensures a valid user can be registered via the serializer,
        and password is hashed.
        """
        data = {
            'username': 'newuser',
            'fullname': 'New User',
            'password': 'securepassword123',
            'role': 'employee'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.fullname, 'New User')
        self.assertEqual(user.role, 'employee')
        self.assertTrue(user.check_password('securepassword123')) 

    def test_registration_with_default_role(self):
        """
        Ensures registration works with a default role if not provided.
        """
        data = {
            'username': 'defaultroleuser',
            'fullname': 'Default Role User',
            'password': 'defaultpassword123',
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.role, 'employee') 

    def test_invalid_registration_missing_username(self):
        """
        Ensures registration fails if username is missing.
        """
        data = {
            'fullname': 'Missing Username',
            'password': 'password123',
            'role': 'manager'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

class UserSerializerTest(TestCase):
    """
    Tests for the UserSerializer.
    """

    def setUp(self):
        """
        Set up a user for serialization tests.
        """
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
        expected_data = {
            'id': self.user.id,
            'username': 'serializertest',
            'fullname': 'Serializer Test User',
            'role': 'manager'
        }
        self.assertEqual(serializer.data, expected_data)

# --- View Tests ---
class RegisterViewTest(APITestCase):
    """
    Tests for the RegisterView (user registration API).
    """

    def test_register_new_user(self):
        """
        Ensures a new user can be registered via the API.
        """
        url = reverse('auth_register')
        data = {
            'username': 'apiregister',
            'fullname': 'API Register User',
            'password': 'apipassword123',
            'role': 'employee'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='apiregister')
        self.assertEqual(user.fullname, 'API Register User')
        self.assertEqual(user.role, 'employee')
        self.assertTrue(user.check_password('apipassword123'))

    def test_register_user_with_default_role(self):
        """
        Ensures a new user can be registered without specifying a role.
        """
        url = reverse('auth_register')
        data = {
            'username': 'apidefaultrole',
            'fullname': 'API Default Role User',
            'password': 'apipassword456',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='apidefaultrole')
        self.assertEqual(user.role, 'employee') 

    def test_register_existing_username(self):
        """
        Ensures registration fails if the username already exists.
        """
        User.objects.create_user(username='existinguser', password='password')
        url = reverse('auth_register')
        data = {
            'username': 'existinguser',
            'fullname': 'Existing User',
            'password': 'newpassword',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class UserViewSetTest(APITestCase):
    """
    Tests for the UserViewSet (CRUD operations for users).
    """

    def setUp(self):
        """
        Create a test user and an admin user for authentication.
        """
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
        self.user2 = User.objects.create_user(
            username='user2',
            fullname='User Two',
            password='user2pass',
            role='manager'
        )
        self.list_url = reverse('user-list')
        self.detail_url = reverse('user-detail', args=[self.user1.id])

    def test_list_users(self):
        """
        Ensures an authenticated user can list all users.
        """
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) 

    def test_retrieve_user(self):
        """
        Ensures an authenticated user can retrieve a single user by ID.
        """
        response = self.client.get(self.detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')
        self.assertEqual(response.data['fullname'], 'User One')

    def test_update_user(self):
        """
        Ensures an authenticated user can update another user's details.
        """
        data = {'fullname': 'Updated User One', 'role': 'manager'}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.fullname, 'Updated User One')
        self.assertEqual(self.user1.role, 'manager')

    def test_delete_user(self):
        """
        Ensures an authenticated user can delete another user.
        """
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 2) 
        self.assertFalse(User.objects.filter(id=self.user1.id).exists())

    def test_unauthenticated_access_to_user_list(self):
        """
        Ensures unauthenticated users cannot access the user list.
        """
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
