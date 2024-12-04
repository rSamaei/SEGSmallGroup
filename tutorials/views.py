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

from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorMatchForm, NewAdminForm,RequestSessionForm, SelectTutorForInvoice, SelectStudentsForInvoice

from tutorials.helpers import login_prohibited

from tutorials.models import RequestSession, TutorSubject, User, Match, RequestSessionDay, Frequency, Invoice
from datetime import date, timedelta
from collections import defaultdict

import calendar as pycalendar
from .forms import AddTutorSubjectForm
from django.utils.timezone import now
from django.db import IntegrityError


@login_required
def dashboard(request):
    """Display dashboard based on user type."""
    current_user = request.user
    context = {'user': current_user}

    if current_user.is_admin:
        total_users_count = User.objects.count()
        unmatched_count = RequestSession.objects.filter(match__isnull=True).count()
        pending_approvals_count = Match.objects.filter(tutor_approved=False).count()
        matched_requests_count = Match.objects.filter(tutor_approved=True).count()

        context.update({
            'unmatched_count': unmatched_count,
            'is_admin_view': True,
            'total_users_count': total_users_count,
            'matched_requests_count': matched_requests_count,
            'pending_approvals_count': pending_approvals_count,
        })  

    elif current_user.is_tutor:
        total_subjects_count = TutorSubject.objects.filter(tutor=current_user).count()
        matched_requests_count = Match.objects.filter(tutor=current_user, tutor_approved=True).count()
        pending_approvals_count = Match.objects.filter(tutor=current_user, tutor_approved=False).count()

        context.update(get_calendar_context(current_user))
        context.update({
            'total_subjects_count': total_subjects_count,
            'is_tutor_view': True,
            'matched_requests_count': matched_requests_count,
            'pending_approvals_count': pending_approvals_count,
        })

    else:
        # Student view context
        unmatched_student_requests = RequestSession.objects.filter(
            student=current_user,
            match__isnull=True
        ).count()
        matched_requests_count = Match.objects.filter(request_session__student=current_user, tutor_approved=True).count()

        context.update(get_calendar_context(current_user))
        context.update({
            'unmatched_student_requests': unmatched_student_requests,
            'is_student_view': True,
            'matched_requests_count': matched_requests_count,
        })

    return render(request, 'dashboard.html', context)


@login_required
def view_matched_requests(request):
    """Display a table of matched requests for a tutor, student, or admin."""
    
    if request.user.is_admin:
        # Admin can see all approved matched requests
        matched_requests = Match.objects.filter(tutor_approved=True)
    elif request.user.is_tutor:
        # Tutors can see only approved matches where they are the tutor
        matched_requests = Match.objects.filter(tutor=request.user, tutor_approved=True)
    else:
        # Students can see only approved matches where they are the student
        matched_requests = Match.objects.filter(request_session__student=request.user, tutor_approved=True)
    
    # Fetch the relevant details to be shown in the table
    matched_requests_data = [
        {
            'tutor': match.tutor.username,
            'student': match.request_session.student.username,
            'subject': match.request_session.subject.name,
            'student_proficiency': match.request_session.proficiency,
            'date_requested': match.request_session.date_requested,
            'frequency': Frequency.to_string(match.request_session.frequency),
        }
        for match in matched_requests
    ]
    
    return render(request, 'view_matched_requests.html', {'matched_requests_data': matched_requests_data})


@login_required
def view_all_tutor_subjects(request):
    # Display all the subjects a tutor is available to teach.
    current_user = request.user
    if not current_user.is_tutor:
        return redirect('dashboard')

    all_subjects = TutorSubject.objects.filter(tutor=current_user)

    if request.method == 'POST':
        form = AddTutorSubjectForm(request.POST)
        if form.is_valid():
            new_subject = form.save(commit=False)
            # Ensure the tutor field is set to the current user.
            new_subject.tutor = current_user
            new_subject.save()
            messages.success(request, 'New subject added successfully!')
            return redirect('view_all_tutor_subjects')
        else:
            messages.error(request, 'Error adding subject. Please try again.')
    else:
        form = AddTutorSubjectForm(initial={'tutor': current_user})

    context = {
        'all_subjects': all_subjects,
        'form': form,
    }
    return render(request, 'view_all_tutor_subjects.html', context)

@login_required
def add_new_subject(request):
    """Display a form to allow tutors to add a new subject."""
    current_user = request.user
    if not current_user.is_tutor:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AddTutorSubjectForm(request.POST)
        if form.is_valid():
            new_subject = form.save(commit=False)
            # Ensure the tutor field is set to the current user
            new_subject.tutor = current_user
            new_subject.save()
            messages.success(request, 'New subject added successfully!')
            return redirect('view_all_tutor_subjects')
        else:
            messages.error(request, 'Error adding subject. Please try again.')
    else:
        form = AddTutorSubjectForm(initial={'tutor': current_user})

    context = {'form': form}
    return render(request, 'add_new_subject.html', context)

@login_required
def calendar_view(request):
    """Display a full calendar with matched schedules."""
    current_user = request.user

    # Get month, year and filter parameters from request
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    selected_user = request.GET.get('user')

    # Use the helper function to get calendar context
    calendar_context = get_calendar_context(current_user, month, year, selected_user)

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
        'users': User.objects.exclude(user_type='admin') if current_user.is_admin else None,  # exclude admins from user timetables
        'selected_user': selected_user,  # the selected user for the timetable from the admin
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
def student_submits_request(request):
    """View for a student to submit a new session request."""
    if not request.user.is_student:
        return redirect('student_view_unmatched_requests')

    if request.method == 'POST':
        form = RequestSessionForm(request.POST, student=request.user)  # Pass student here
        if form.is_valid():
            try:
                new_request = form.save(commit=False)
                new_request.student = request.user
                new_request.date_requested = now().date()
                new_request.save()
                # Assuming you're handling days elsewhere
                return redirect('student_view_unmatched_requests')
            except IntegrityError:
                messages.error(request, "You have already submitted a request for this subject.")
    else:
        form = RequestSessionForm(student=request.user)  # Pass student here

    return render(request, 'student_submits_request.html', {'form': form})




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
def delete_tutor_subject(request, subject_id):
    """Delete a tutor's subject from the system."""
    # Ensure the user is the tutor who owns the subject
    subject = get_object_or_404(TutorSubject, id=subject_id)
    
    # Check if the logged-in user is the tutor who owns this subject
    if subject.tutor != request.user:
        return redirect('view_all_tutor_subjects')  # Redirect if the tutor doesn't own the subject
    
    # Delete the subject
    subject.delete()

    # Redirect back to the tutor's subjects page
    return redirect('view_all_tutor_subjects')

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
def pending_approvals(request):
    """List pending matches for tutors or admins."""
    current_user = request.user

    if current_user.is_admin:
        # Admin: See all pending requests
        matches = Match.objects.filter(tutor_approved=False)
        can_approve = False  # Admins cannot approve requests
    elif current_user.is_tutor:
        # Tutor: See only their pending requests
        matches = Match.objects.filter(tutor=current_user, tutor_approved=False)
        can_approve = True  # Tutors can approve their requests
    else:
        # Redirect non-admins and non-tutors
        return redirect('dashboard')

    matches_data = [
        {
            'id': match.id,
            'student': match.request_session.student.username,
            'tutor_username': match.tutor.username,
            'subject': match.request_session.subject.name,
            'proficiency': match.request_session.proficiency,
            'frequency': Frequency.to_string(match.request_session.frequency),
            'date_requested': match.request_session.date_requested,
        }
        for match in matches
    ]

    return render(
        request,
        'pending_approvals.html',
        {'matches_data': matches_data, 'can_approve': can_approve}
    )

@login_required
def approve_match(request, match_id):
    """Approve a match, setting tutor_approved=True."""
    if not request.user.is_tutor:
        return redirect('dashboard')  # Only tutors can approve matches

    try:
        match = Match.objects.get(id=match_id, tutor=request.user)
    except Match.DoesNotExist:
        # Match doesn't exist or isn't assigned to this tutor
        return redirect('pending_approvals')

    if request.method == "POST":
        # Approve the match
        match.tutor_approved = True
        match.save()
        generateInvoice(Match.objects.get(id = match_id))
        messages.success(request, "Match approved successfully.")
        return redirect('pending_approvals')

    return redirect('dashboard')



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
                tempMatch = form.save(request_session=session)
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
    if not request.user.is_admin:
        return redirect('dashboard')
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
    if request.user.is_admin:
        if request.method == "GET":
            form = SelectTutorForInvoice(request.GET)
            if form.is_valid():
                selectedTutor = form.cleaned_data.get('tutor')
                allMatches = Match.objects.filter(
                    tutor=selectedTutor,
                    tutor_approved=True  # Only approved matches
                )
                listOfPaidInvoice = []
                listOfUnpaidInvoices = []
                for match in allMatches:
                    inv = Invoice.objects.filter(match = match)
                    if(inv[0].payment_status == 'paid'):
                        listOfPaidInvoice.append(inv[0])
                    else:
                        listOfUnpaidInvoices.append(inv[0])
                context = {'form' : form, 'paid_sessions': listOfPaidInvoice, 'unpaid_sessions' : listOfUnpaidInvoices}
                return render(request, 'invoice.html', context)
            else:
                form = SelectTutorForInvoice()
                context = {'form' : form, 'paid_sessions':None}
                return render(request, 'invoice.html', context)

        elif request.method == "POST":
            paymentMatchID = request.POST['session']
            session_match = get_object_or_404(Match, id=paymentMatchID)
            tempInvoice = Invoice.objects.get(
                match = session_match
            )
            tempInvoice.payment_status = 'paid'
            tempInvoice.save()
            

            form = SelectTutorForInvoice()
            context = {'form' : form, 'paid_sessions':None}
            return render(request, 'invoice.html', context)

        else:
            form = SelectTutorForInvoice()
            context = {'form' : form, 'paid_sessions':None}
            return render(request, 'invoice.html', context)

    elif request.user.is_tutor:
        allMatches = Match.objects.filter(
            tutor=request.user,
            tutor_approved=True  # Only approved matches
        )
        listOfPaidInvoice = []
        listOfUnpaidInvoices = []
        for match in allMatches:
            inv = Invoice.objects.filter(match = match)
            if(inv[0].payment_status == 'paid'):
                listOfPaidInvoice.append(inv[0])
            else:
                listOfUnpaidInvoices.append(inv[0])
        context = {'form' : form, 'paid_sessions': listOfPaidInvoice, 'unpaid_sessions' : listOfUnpaidInvoices}
        return render(request, 'invoice.html', context)

    elif request.user.is_student:
        if request.method == "POST":
            paymentMatchID = request.POST['session']
            session_match = get_object_or_404(Match, id=paymentMatchID)
            tempInvoice = Invoice.objects.get(
                match = session_match
            )
            tempInvoice.payment_status = 'waiting'
            tempInvoice.save()

        allMatches = Match.objects.filter(
            request_session__student=request.user,
            tutor_approved=True  # Only approved matches
        )
        listOfPaidInvoice = []
        listOfUnpaidInvoices = []
        for match in allMatches:
            inv = Invoice.objects.filter(match = match)
            if(inv[0].payment_status == 'unpaid'):
                listOfUnpaidInvoices.append(inv[0])
            else:
                listOfPaidInvoice.append(inv[0])
        context = {'form' : form, 'paid_sessions': listOfPaidInvoice, 'unpaid_sessions' : listOfUnpaidInvoices}
        return render(request, 'invoice.html', context)


def generateInvoice(session_match: Match):
    if not session_match.tutor_approved:
        return
    
    selectedTutor = session_match.tutor
    tutorSub = TutorSubject.objects.filter(
        tutor=selectedTutor,
        subject=session_match.request_session.subject,
    )
    if tutorSub.exists():
        tempPrice = round(tutorSub[0].price * 27 * session_match.request_session.frequency, 2)
        Invoice.objects.create(
            match=session_match,
            payment=tempPrice
        )
  

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

    request_date = session.date_requested
    if(session.frequency == 2.0):
        interlude = 1
    else:
        interlude = int(7 / session.frequency)

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
            dates.append(current.day + 1)
            current += timedelta(days=interlude)
        else:
            current += timedelta(days=1)
    
    """so basically the dates are being added as the actual number days
        so if the date is 2022-01-01, the day is being added as 1
        calendar will then cycle through the calendar which is just a table with numbers and add it in if the number is the same"""

    return dates

def get_calendar_context(user, month=None, year=None, selected_user=None):
    """Get calendar context for the user."""
    if month is None:
        month = date.today().month
    if year is None:
        year = date.today().year

    # Filter sessions based on user type with tutor_approved check
    if user.user_type == 'student':
        sessions = RequestSession.objects.filter(
            student=user,
            match__isnull=False,
            match__tutor_approved=True
        ).select_related('match', 'subject', 'match__tutor').prefetch_related('days')
    elif user.user_type == 'tutor':
        sessions = RequestSession.objects.filter(
            match__tutor=user,
            match__tutor_approved=True
        ).select_related('match', 'subject', 'student').prefetch_related('days')
    else:
        # Admin view with optional user filter
        if selected_user:
            selected_user_obj = User.objects.get(username=selected_user)
            if selected_user_obj.is_student:
                sessions = RequestSession.objects.filter(
                    student=selected_user_obj,
                    match__isnull=False,
                    match__tutor_approved=True
                )
            elif selected_user_obj.is_tutor:
                sessions = RequestSession.objects.filter(
                    match__tutor=selected_user_obj,
                    match__tutor_approved=True
                )
        else:
            sessions = RequestSession.objects.filter(
                match__isnull=False,
                match__tutor_approved=True
            ).select_related('match', 'subject', 'student', 'match__tutor').prefetch_related('days')

    # Get recurring dates for each session
    highlighted_dates = set()
    for session in sessions:
        recurring_dates = get_recurring_dates(session, year, month)
        session.recurring_dates = recurring_dates
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
