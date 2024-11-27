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

    def __str__(self):
        return self.username

    @property
    def is_admin(self) -> bool:
        """Check if user has admin type."""
        return self.user_type == 'admin'
    
    @property
    def is_tutor(self) -> bool:
        """Check if user has tutor type."""
        return self.user_type == 'tutor' 
    
    @property
    def is_student(self) -> bool:
        """Check if user has student type."""
        return self.user_type == 'student'

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

    FREQUENCY_CHOICES = (
        (0.5, 'Fortnightly'),
        (1, 'Weekly'),
        (2, 'Biweekly'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    frequency = models.DecimalField(max_digits=2, decimal_places=1, default=1.0)  # Added default=1 for once per week
    proficiency = models.CharField(max_length=12, choices=PROFICIENCY_TYPES, default='Beginner')
    date_requested = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.username} - {self.subject.name}"
    
class RequestSessionDay(models.Model):
    """Model to represent days associated with a RequestSession."""
    request_session = models.ForeignKey(
        RequestSession,
        on_delete=models.CASCADE,
        related_name='days'
    )
    day_of_week = models.CharField(
        max_length=15,
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
        ]
    )

    def __str__(self):
        return f"{self.request_session} on {self.day_of_week}"


class Match(models.Model):
    """Model for matching requests to tutors"""

    request_session = models.OneToOneField(RequestSession, on_delete=models.CASCADE)
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')

    def __str__(self):
        return f"Match: {self.request_session} with Tutor {self.tutor.username}"


class Invoice(models.Model):
    """Model used to represent invoices"""

    payment = models.DecimalField(max_digits=10, decimal_places=2)
    matchID = models.ForeignKey(Match, on_delete=models.CASCADE)


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
    price  = models.DecimalField(max_digits=4, decimal_places=2, default=10.00)

    class Meta:
        unique_together = ('tutor', 'subject')

    def __str__(self):
        return f"{self.tutor.username} - {self.subject.name}"