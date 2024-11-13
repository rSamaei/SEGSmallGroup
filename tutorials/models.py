from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
        ('admin', 'Admin'),
    )

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')


    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)
    
class Subject(models.Model):
    """Model used to represent subjects which can be taught"""

    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name
    
class RequestSession(models.Model):
    """Model for a session request made by a student"""

    PROFICIENCY_TYPES = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    frequency = models.PositiveIntegerField(default=1)  # Added default=1 for once per week
    proficiency = models.CharField(max_length=12, choices=PROFICIENCY_TYPES, default='Beginner')
    date_requested = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.username} - {self.subject.name}"
    
class Match(models.Model):
    """Model for matching requests to tutors"""

    request_session = models.OneToOneField(RequestSession, on_delete=models.CASCADE)
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')

    def __str__(self):
        return f"Match: {self.request_session} with Tutor {self.tutor.username}"

class TutorSubject(models.Model):
    """Model for tutors and their associated subjects"""
    
    PROFICIENCY_TYPES = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=12, choices=PROFICIENCY_TYPES, default='Beginner')

    class Meta:
        unique_together = ('tutor', 'subject')

    def __str__(self):
        return f"{self.tutor.username} - {self.subject.name}"