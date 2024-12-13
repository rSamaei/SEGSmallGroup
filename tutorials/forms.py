"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.utils import timezone

from django.forms import Select
from .models import User, Match, RequestSession, RequestSessionDay, TutorSubject, Subject, Frequency
from django.core.exceptions import ValidationError

class AddTutorSubjectForm(forms.ModelForm):
    class Meta:
        model = TutorSubject
        fields = ['tutor', 'subject', 'proficiency']
        widgets = {
            'tutor': forms.HiddenInput(),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'proficiency': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'subject': 'Subject',
            'proficiency': 'Proficiency Level',
        }

class UpdateProficiencyForm(forms.ModelForm):
    class Meta:
        model = TutorSubject
        fields = ['proficiency']  # Only the proficiency field is needed
        widgets = {
            'proficiency': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'proficiency': 'Proficiency Level',
        }

class RequestSessionForm(forms.ModelForm):
    """Form for students to create a new session request."""

    days = forms.MultipleChoiceField(
        choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), 
                 ('Thursday', 'Thursday'), ('Friday', 'Friday')],
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = RequestSession
        fields = ['subject', 'proficiency', 'frequency', 'days']
        widgets = {
            'proficiency': forms.Select(choices=RequestSession.PROFICIENCY_TYPES),
            'frequency': forms.Select(choices=RequestSession.FREQUENCY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')

        # Ensure subject is a valid Subject instance
        if isinstance(subject, str):
            subject = Subject.objects.filter(name=subject).first()
            if not subject:
                raise ValidationError(f"Subject '{subject}' does not exist.")
        elif not isinstance(subject, Subject):
            raise ValidationError("Invalid subject selected.")

        # Ensure a student is provided
        if not self.student:
            raise ValidationError("Student information is missing.")

        # Check for duplicate requests
        if RequestSession.objects.filter(student=self.student, subject=subject).exists():
            raise ValidationError("You have already submitted a request for this subject.")

        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.date_requested:
            instance.date_requested = timezone.now()  # set to current date/time 
        if commit:
            instance.save()
        return instance

    def clean_frequency(self):
        frequency = self.cleaned_data.get('frequency')

        if frequency is None:  # No frequency selected
            raise ValidationError("You must select a frequency.")
        
        return frequency


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
    """
    tutor = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )

    def __init__(self, request_session: RequestSession, *args, **kwargs) -> None:
        """Initialize form with filtered tutor queryset based on request requirements."""
        super().__init__(*args, **kwargs)

        # Define proficiency levels in order of hierarchy
        proficiency_hierarchy = {'beginner': 1,'intermediate': 2,'advanced': 3}

        # Get the requested proficiency level and normalize it to lowercase
        requested_proficiency = request_session.proficiency.lower()

        self.fields['tutor'].queryset = User.objects.filter(
            user_type='tutor',
            tutor_subjects__subject=request_session.subject,
            tutor_subjects__proficiency__in=[
                prof.capitalize() for prof, level in proficiency_hierarchy.items()
                if level >= proficiency_hierarchy[requested_proficiency]
            ]
        ).distinct()


    def save(self, request_session: RequestSession) -> Match:
        """Save the match to the database."""
        tutor = self.cleaned_data['tutor']
        match = Match.objects.create(
            request_session=request_session,
            tutor=tutor,
            tutor_approved=False
        )

        for day in request_session.days.all():
            RequestSessionDay.objects.create(
                request_session=request_session,
                day_of_week=day.day_of_week
            )
        
        return match
    
    def clean_tutor(self):
        tutor = self.cleaned_data.get('tutor')
        if not tutor:
            raise ValidationError("A valid tutor must be selected.")
        return tutor
      
class NewAdminForm(NewPasswordMixin, forms.ModelForm):
    """Form to create new admin."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

class SelectTutorForInvoice(forms.Form):
    tutor = forms.ModelChoiceField(
        queryset=None, 
        empty_label="Unselected",
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        matched_user_ids = Match.objects.filter(
            tutor_approved=True  # Only include approved matches
        ).values_list('tutor_id', flat=True)
        self.fields['tutor'].queryset = User.objects.filter(id__in=matched_user_ids).distinct()

class PayInvoice(forms.Form):
    """Form for submitting invoice payments with bank transfer details."""
    
    bank_transfer = forms.CharField(
        label="Bank Transfer Number",
        max_length=34,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'GB12BANK12345612345678'
        })
    )

    session = forms.IntegerField(
        widget=forms.HiddenInput()
    )

    def clean_bank_transfer(self):
        bank_transfer = self.cleaned_data.get('bank_transfer')
        if not bank_transfer:
            raise ValidationError("Bank transfer number is required")
        return bank_transfer.strip()
