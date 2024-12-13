from django import forms
from django.test import TestCase
from tutorials.forms import NewAdminForm
from tutorials.models import User

class AdminFormTestCase(TestCase):
    def setUp(self):
        self.form_input = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'username': '@janedoe',
            'email': 'janedoe@example.org',
            'new_password': 'Password123',
            'password_confirmation': 'Password123'
        }
    
    def test_signIn(self):
        self.form = NewAdminForm(data=self.form_input)
        self.user = User.objects.create_user(
                    username = self.form_input.get('username'),
                    first_name=self.form_input.get('first_name'),
                    last_name=self.form_input.get('last_name'),
                    email=self.form_input.get('email'),
                    password=self.form_input.get('new_password'),
                    user_type = 'admin',
                )
        self.user.save()
        self.tempUser = User.objects.filter(first_name='Jane').first()
        
        self.assertEqual(self.tempUser.user_type,'admin')
