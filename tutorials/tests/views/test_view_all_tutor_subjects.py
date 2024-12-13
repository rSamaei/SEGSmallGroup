from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from tutorials.models import User, Subject, TutorSubject
from tutorials.forms import AddTutorSubjectForm

class ViewAllTutorSubjectsTest(TestCase):
    """Tests for the view_all_tutor_subjects view."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
    ]

    def setUp(self):
        self.tutor = User.objects.filter(user_type='tutor').first()
        self.student = User.objects.filter(user_type='student').first()
        self.subject = Subject.objects.first()
        self.client = Client()

    def test_redirect_if_not_tutor(self):
        """Test non-tutors are redirected to dashboard"""
        self.client.login(username=self.student.username, password='Password123')
        response = self.client.get(reverse('view_all_tutor_subjects'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_get_view_all_tutor_subjects(self):
        """Test GET request displays tutor's subjects"""
        self.client.login(username=self.tutor.username, password='Password123')
        TutorSubject.objects.create(
            tutor=self.tutor,
            subject=self.subject,
            proficiency='Advanced'
        )
        
        response = self.client.get(reverse('view_all_tutor_subjects'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_all_tutor_subjects.html')
        self.assertEqual(len(response.context['all_subjects']), 1)
        self.assertIsInstance(response.context['form'], AddTutorSubjectForm)

    def test_post_add_subject_invalid_form(self):
        """Test invalid form submission"""
        self.client.login(username=self.tutor.username, password='Password123')
        
        response = self.client.post(reverse('view_all_tutor_subjects'), {
            'subject': '',  # Invalid - subject is required
            'proficiency': 'Advanced'
        })
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Error adding subject. Please try again.')
        self.assertFalse(TutorSubject.objects.filter(tutor=self.tutor).exists())

    def test_only_shows_current_tutor_subjects(self):
        """Test that only current tutor's subjects are shown"""
        other_tutor = User.objects.create_user(
            username='@othertutor',
            password='Password123',
            user_type='tutor'
        )
        
        # Create subjects for both tutors
        TutorSubject.objects.create(
            tutor=self.tutor,
            subject=self.subject,
            proficiency='Advanced'
        )
        TutorSubject.objects.create(
            tutor=other_tutor,
            subject=self.subject,
            proficiency='Beginner'
        )
        
        self.client.login(username=self.tutor.username, password='Password123')
        response = self.client.get(reverse('view_all_tutor_subjects'))
        
        self.assertEqual(len(response.context['all_subjects']), 1)
        self.assertEqual(response.context['all_subjects'][0].tutor, self.tutor)