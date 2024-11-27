from itertools import cycle
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorMatchForm, NewAdminForm, SelectTutorForInvoice
from tutorials.helpers import login_prohibited
from tutorials.models import RequestSession, TutorSubject, User, Match, RequestSessionDay, Invoice
from datetime import date

from collections import defaultdict
import calendar as pycalendar



@login_required
def dashboard(request):
    """Display dashboard based on user type."""
    current_user = request.user
    context = {'user': current_user}

    if (current_user.is_admin):
        # Get count of unmatched requests
        unmatched_count = RequestSession.objects.filter(
            match__isnull=True
        ).count()
        
        context.update({
            'unmatched_count': unmatched_count,
            'is_admin_view': True
        })
    else:
        # Add calendar context for non-admin users
        context.update(get_calendar_context(current_user))

    return render(request, 'dashboard.html', context)

@login_required
def calendar_view(request):
    """Display a full calendar with matched schedules."""
    current_user = request.user

    # Use the helper function to get calendar context
    calendar_context = get_calendar_context(current_user)

    # Add additional details for the full calendar view
    from datetime import date
    today = date.today()
    context = {
        'calendar_month': calendar_context['calendar_month'],
        'highlighted_dates': calendar_context['highlighted_dates'],
        'month_name': today.strftime('%B'),
        'year': today.year,
    }

    return render(request, 'calendar.html', context)

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

@login_required
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



@login_required
def invoice(request):
    form = None
    if request.method == "GET":
        form = SelectTutorForInvoice(request.GET)
        if form.is_valid():
            selectedTutor = form.cleaned_data.get('tutor')
            allMatches = Match.objects.filter(
                tutor = selectedTutor
            )
            count = allMatches.count()
            listOfSessions = None

            if count > 0:
                listOfSessions = {}
                for match in allMatches:
                    tutorSub = TutorSubject.objects.filter(
                        tutor = selectedTutor,
                        subject = match.request_session.subject,
                    )
                    listOfSessions[match] = round(tutorSub[0].price * 27 * match.request_session.frequency, 2)
    
            

            context = {'form' : form, 'request_sessions':listOfSessions}
            return render(request, 'invoice.html', context)
        else:
            form = SelectTutorForInvoice()
            context = {'form' : form, 'request_sessions':None}
            return render(request, 'invoice.html', context)

    elif request.method == "POST":
        price = request.POST['price']
        matchID = request.POST['session']
        print(matchID)
        session_match = get_object_or_404(Match, id=matchID)
        
        try:
            tempInvoice = Invoice.objects.create(
                match = session_match,
                payment = price
            )
        except Exception as e:
            print(e)
            form = SelectTutorForInvoice()
            context = {'form' : form, 'request_sessions':None}
            return render(request, 'invoice.html', context)

        form = SelectTutorForInvoice()
        context = {'form' : form, 'request_sessions':None}
        return render(request, 'invoice.html', context)
        

    else:
        form = SelectTutorForInvoice()
        context = {'form' : form, 'request_sessions':None}
        return render(request, 'invoice.html', context)
    
    
    








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

def get_calendar_context(user):
    """Generate the calendar context for the user dashboard."""
    # Define a color palette for different sessions
    colors = cycle(['#FFD700', '#FF8C00', '#1E90FF', '#32CD32', '#FF69B4', '#7B68EE'])

    # Get the current month and year
    today = date.today()
    cal = pycalendar.Calendar(firstweekday=0)
    calendar_month = cal.monthdayscalendar(today.year, today.month)

    # Fetch all matched sessions for this user
    matched_sessions = RequestSessionDay.objects.filter(
        request_session__match__tutor=user,
        request_session__match__isnull=False  # Ensure there's a match
    ).select_related('request_session')

    # Dictionary to store color for each session ID
    session_colors = {}
    for session in matched_sessions:
        if session.request_session.id not in session_colors:
            session_colors[session.request_session.id] = next(colors)

    # Prepare a dictionary of highlighted dates
    highlighted_dates = {}
    for session_day in matched_sessions:
        day_of_week = session_day.day_of_week

        # Find all days of this weekday in the current month
        for week in calendar_month:
            if week[day_of_week]:  # if day is not 0, i.e., it exists in the month
                day = week[day_of_week]
                if day not in highlighted_dates:
                    highlighted_dates[day] = []
                highlighted_dates[day].append(session_colors[session_day.request_session.id])

    # Return the prepared calendar context
    return {
        'calendar_month': calendar_month,
        'highlighted_dates': highlighted_dates,
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
