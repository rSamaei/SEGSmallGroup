from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class ViewAllUsersTestCase(TestCase):
    
    def setUp(self):
        # Get the custom User model
        User = get_user_model()

        # Create an admin user by explicitly setting the 'user_type' to 'admin'
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='password123',
            first_name='Admin',
            last_name='User',
            email='adminuser@example.com',
            user_type='admin'  # Explicitly set user_type to 'admin'
        )
        
        # Ensure the admin user is marked as a superuser as well (optional, for broader admin access)
        self.admin_user.is_superuser = True
        self.admin_user.is_staff = True
        self.admin_user.save()

        # Create normal users
        self.user1 = User.objects.create_user(
            username='user1',
            password='password123',
            first_name='John',
            last_name='Doe',
            email='user1@example.com'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='password123',
            first_name='Jane',
            last_name='Doe',
            email='user2@example.com'
        )

        # URL for the view_all_users page
        self.url = reverse('view_all_users')

    def test_redirect_for_non_admin_user(self):
        """Test that non-admin users are redirected."""
        # Create a non-admin user
        self.client.login(username='user1', password='password123')
        
        # Check if non-admin users are redirected
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_access(self):
        """Test that admin users can access the page."""
        self.client.login(username='adminuser', password='password123')
        
        # Check if the response is successful
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_all_users.html')

    def test_user_list_display(self):
        """Test that the user list is rendered correctly."""
        self.client.login(username='adminuser', password='password123')
        
        # Get the response
        response = self.client.get(self.url)
        
        # Check if all users are rendered in the template
        self.assertContains(response, 'John')
        self.assertContains(response, 'Jane')
        self.assertContains(response, 'user1@example.com')
        self.assertContains(response, 'user2@example.com')

    def test_search_functionality(self):
        """Test that search functionality works correctly."""
        self.client.login(username='adminuser', password='password123')

        # Search for "John"
        response = self.client.get(self.url, {'search': 'John'})
        self.assertContains(response, 'John')
        self.assertNotContains(response, 'Jane')
        
        # Search for "Doe"
        response = self.client.get(self.url, {'search': 'Doe'})
        self.assertContains(response, 'John')
        self.assertContains(response, 'Jane')

        # Search for "user1" (username)
        response = self.client.get(self.url, {'search': 'user1'})
        self.assertContains(response, 'user1')
        self.assertNotContains(response, 'user2')

    def test_no_users_found(self):
        """Test that "No users found" message is displayed when no search results match."""
        self.client.login(username='adminuser', password='password123')

        # Perform a search with a term that matches no users
        response = self.client.get(self.url, {'search': 'nonexistentuser'})
        
        # Check if the message "No users found" appears
        self.assertContains(response, 'No users found.')

    def test_user_deletion(self):
        """Test that a user can be deleted."""
        self.client.login(username='adminuser', password='password123')

        # Create a new user to delete
        user_to_delete = get_user_model().objects.create_user(
            username='deleteuser',
            password='password123',
            first_name='Delete',
            last_name='User',
            email='deleteuser@example.com'
        )
        
        # Ensure the user exists in the database
        self.assertTrue(get_user_model().objects.filter(username='deleteuser').exists())

        # Send a POST request to delete the user
        response = self.client.post(reverse('delete_user', args=[user_to_delete.id]))
        
        # Check that the user has been deleted
        self.assertFalse(get_user_model().objects.filter(username='deleteuser').exists())