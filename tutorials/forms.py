"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator

from django.forms import Select
from .models import User, Match, RequestSession, RequestSessionDay

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user


class UserForm(forms.ModelForm):
    """Form to update user profiles."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

class NewPasswordMixin(forms.Form):
    """Form mixing for new_password and password_confirmation fields."""

    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
        validators=[RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$',
            message='Password must contain an uppercase character, a lowercase '
                    'character and a number'
            )]
    )
    password_confirmation = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    def clean(self):
        """Form mixing for new_password and password_confirmation fields."""

        super().clean()
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password != password_confirmation:
            self.add_error('password_confirmation', 'Confirmation does not match password.')


class PasswordForm(NewPasswordMixin):
    """Form enabling users to change their password."""

    password = forms.CharField(label='Current password', widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        
        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Clean the data and generate messages for any errors."""

        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is invalid")

    def save(self):
        """Save the user's new password."""

        new_password = self.cleaned_data['new_password']
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user


class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Form enabling unregistered users to sign up."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def save(self):
        """Create a new user."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        return user

class TutorMatchForm(forms.Form):
    """
    A form for matching tutors with request sessions based on subject and proficiency.
    This form provides a single ModelChoiceField for selecting a tutor from a filtered
    queryset of users who:
        1. Have the user type 'tutor'
        2. Match the subject of the request session
        3. Match the proficiency level of the request session
    Attributes:
        tutor (ModelChoiceField): A dropdown field for selecting a tutor with 
            Bootstrap styling.
    Args:
        request_session: The session request object containing subject and 
            proficiency requirements.
    """
    tutor = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )

    def __init__(self, request_session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tutor'].queryset = User.objects.filter(
            user_type='tutor',
            tutor_subjects__subject=request_session.subject,
            tutor_subjects__proficiency=request_session.proficiency
        ).distinct()

class RequestSessionForm(forms.ModelForm):
    """Form for creating or updating RequestSession with multiple days."""

    days = forms.MultipleChoiceField(
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
        ],
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = RequestSession
        fields = ['subject', 'proficiency', 'days']
        widgets = {
            'frequency': Select(attrs={'class': 'form-select'}),
        }

    def save_days(self, request_session, days):
        """Save the selected days to the RequestSessionDay model."""
        # Clear existing days
        RequestSessionDay.objects.filter(request_session=request_session).delete()
        # Add new days
        for day in days:
            RequestSessionDay.objects.create(request_session=request_session, day_of_week=day)
