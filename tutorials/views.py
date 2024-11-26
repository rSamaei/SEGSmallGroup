from itertools import cycle
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorMatchForm, NewAdminForm
from tutorials.helpers import login_prohibited
from tutorials.models import RequestSession, TutorSubject, User, Match, RequestSessionDay
from datetime import date, timedelta
import calendar as pycalendar

@login_required
def dashboard(request):
    """Display dashboard based on user type."""
    current_user = request.user
    context = {'user': current_user}

    if current_user.is_admin:
        # Get count of unmatched requests
        unmatched_count = RequestSession.objects.filter(
            match__isnull=True
        ).count()

        # Get information for the users box
        total_users_count = User.objects.count()

        context.update({
            'unmatched_count': unmatched_count,
            'is_admin_view': True,
            'total_users_count': total_users_count,
        })
    else:
        # Get the count of the current user's unmatched requests
        unmatched_student_requests = RequestSession.objects.filter(
            student=current_user,
            match__isnull=True
        ).count()

        # Add calendar context for non-admin users
        context.update(get_calendar_context(current_user))
        context.update({
            'unmatched_student_requests': unmatched_student_requests,
            'is_student_view': current_user.is_student,
        })

    return render(request, 'dashboard.html', context)

@login_required
def calendar_view(request):
    """Display a full calendar with matched schedules."""
    current_user = request.user

    # Get month and year from request parameters
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))

    # Use the helper function to get calendar context
    calendar_context = get_calendar_context(current_user, month, year)

    # Calculate previous and next month
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'calendar_month': calendar_context['calendar_month'],
        'highlighted_dates': calendar_context['highlighted_dates'],
        'sessions': calendar_context['sessions'],
        'month_name': date(year, month, 1).strftime('%B'),
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }

    return render(request, 'calendar.html', context)

@login_required
def student_view_unmatched_requests(request):
    """Display unmatched requests for the logged-in student."""
    current_user = request.user

    # Ensure the user is a student
    if not current_user.is_student:
        return redirect('dashboard')  # Redirect non-students to their dashboard

    unmatched_requests = RequestSession.objects.filter(
        student=current_user,
        match__isnull=True
    )

    context = {
        'unmatched_requests': unmatched_requests
    }
    return render(request, 'student_view_unmatched_requests.html', context)


@login_required
def view_all_users(request):
    """Display all users in a separate page."""
    current_user = request.user
    if not current_user.is_admin:
        # Redirect to dashboard if the user is not an admin
        return redirect('dashboard')

    all_users = User.objects.all()
    context = {'all_users': all_users}
    return render(request, 'view_all_users.html', context)

@login_required
def admin_requested_sessions(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    
    # query for unmatched requests, select related performs a join on the student and subject tables to find 
    unmatched_requests = RequestSession.objects.filter(
        match__isnull=True
    ).select_related('student', 'subject')
    
    # Create a form for each request
    requests_with_forms = []
    for req in unmatched_requests:
        requests_with_forms.append({
            'request': req,
            'form': TutorMatchForm(req)
        })
    
    # Render the admin requested sessions template with the requests and forms
    return render(request, 'admin_requested_sessions.html', {
        'requests_with_forms': requests_with_forms,
        'is_admin_view': True
    })

@login_required
def admin_requested_session_highlighted(request, request_id):
    """Display detailed view of a specific request."""
    if not request.user.is_admin:
        return redirect('dashboard')

    # Fetch the specific request session by ID
    session_request = RequestSession.objects.get(id=request_id)
    
    # Initialize form with request data if submitted
    form = TutorMatchForm(session_request, request.GET or None)
    
    selected_tutor = None
    if form.is_valid():
        # Get the selected tutor from the form
        selected_tutor = form.cleaned_data['tutor']
    
    # Render the detailed view template with the request, form, and selected tutor
    return render(request, 'admin_requested_session_highlighted.html', {
        'request': session_request,
        'form': form,
        'selected_tutor': selected_tutor
    })

@login_required
def create_match(request, request_id):
    """Create a match between request and selected tutor."""
    if not request.user.is_admin:
        return redirect('dashboard')
    
    session = RequestSession.objects.get(id=request_id)
    
    if request.method == 'POST':
        form = TutorMatchForm(session, request.POST)
        if form.is_valid():
            try:
                form.save(request_session=session)
                messages.success(request, 'Match created successfully')
                return redirect('admin_requested_sessions')
            except Exception as e:
                messages.error(request, f'Error creating match: {str(e)}')
        else:
            messages.error(request, 'Invalid form submission')
        return redirect('admin_requested_session_highlighted', request_id=request_id)
    
    return redirect('admin_requested_sessions')

def registerNewAdmin(request):
    form = None
    if request.method == "POST":
       form = NewAdminForm(request.POST) 
       if form.is_valid():
            try:
                user = User.objects.create_user(
                    form.cleaned_data.get('username'),
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name'),
                    email=form.cleaned_data.get('email'),
                    password=form.cleaned_data.get('new_password'),
                    user_type = 'admin',
                )
                user.save()
            except:
                form.add_error(None,"Unable to create")
            else:
                path = reverse('dashboard')
                return HttpResponseRedirect(path)

                   
    else:
        form = NewAdminForm()
    
    return render(request, 'registerAdmin.html', {'form':form})





@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')

def get_recurring_dates(session, year, month):
    """Generate recurring dates based on session frequency and term."""
    dates = []
    
    # Get start and end of current month
    month_start = date(year, month, 1)
    month_end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year + 1, 1, 1) - timedelta(days=1)
    print(month_start, month_end)

    request_date = session.date_requested
    if(session.frequency == 2.0):
        interlude = 1
    else:
        interlude = int(7 / session.frequency)
    print(session.frequency)
    print(interlude)

    # calculate academic year dates based on request_date
    if 9 <= request_date.month <= 12:
        academic_year_start = date(request_date.year, 9, 1)
        academic_year_end = date(request_date.year + 1, 7, 20)
        term_dates = [
            (date(request_date.year, 9, 1), date(request_date.year, 12, 20)),  # Autumn
            (date(request_date.year + 1, 1, 4), date(request_date.year + 1, 3, 31)),  # Spring
            (date(request_date.year + 1, 4, 15), date(request_date.year + 1, 7, 20))  # Summer
        ]
    else:
        academic_year_start = date(request_date.year - 1, 9, 1)
        academic_year_end = date(request_date.year, 7, 20)
        term_dates = [
            (date(request_date.year - 1, 9, 1), date(request_date.year - 1, 12, 20)),  # Autumn
            (date(request_date.year, 1, 4), date(request_date.year, 3, 31)),  # Spring
            (date(request_date.year, 4, 15), date(request_date.year, 7, 20))  # Summer
        ]
    
    # Get session days
    session_days = [day.day_of_week for day in session.days.all()]

    # current = month_start
    current = academic_year_start
    while current <= min(academic_year_end, month_end):
        in_term = any(term_start <= current <= term_end for term_start, term_end in term_dates)

        if in_term and pycalendar.day_name[current.weekday()] in session_days and current.month == month:
            print(pycalendar.day_name[current.weekday()], ", session days: ", session_days)
            dates.append(current.day + 1)
            current += timedelta(days=interlude)
        else:
            current += timedelta(days=1)
    
    """so basically the dates are being added as the actual number days
        so if the date is 2022-01-01, the day is being added as 1
        calendar will then cycle through the calendar which is just a table with numbers and add it in if the number is the same"""

    return dates

def get_calendar_context(user, month=None, year=None):
    """Get calendar context for the user."""
    if month is None:
        month = date.today().month
    if year is None:
        year = date.today().year
    
    # Filter sessions based on user type
    if user.user_type == 'student':
        sessions = RequestSession.objects.filter(
            student=user,
            match__isnull=False
        ).select_related('match', 'subject', 'match__tutor').prefetch_related('days')
    elif user.user_type == 'tutor':
        sessions = RequestSession.objects.filter(
            match__tutor=user
        ).select_related('match', 'subject', 'student').prefetch_related('days')
    else:
        sessions = RequestSession.objects.filter(
            match__isnull=False
        ).select_related('match', 'subject', 'student', 'match__tutor').prefetch_related('days')

    # Get recurring dates for each session
    highlighted_dates = set()
    for session in sessions:
        recurring_dates = get_recurring_dates(session, year, month)
        session.recurring_dates = recurring_dates  # Add to session object
        highlighted_dates.update(recurring_dates)
    
    return {
        'calendar_month': pycalendar.monthcalendar(year, month),
        'highlighted_dates': highlighted_dates,
        'sessions': sessions
    }

class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)
