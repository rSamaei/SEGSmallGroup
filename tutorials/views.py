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
from django.db.models import Q

from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorMatchForm, NewAdminForm,RequestSessionForm, SelectTutorForInvoice, SelectStudentsForInvoice, UpdateProficiencyForm

from tutorials.helpers import login_prohibited

from tutorials.models import RequestSession, TutorSubject, User, Match, RequestSessionDay, Frequency, Invoice
from datetime import date, timedelta

import calendar as pycalendar
from .forms import AddTutorSubjectForm
from django.utils.timezone import now
from django.db import IntegrityError
from django.core.paginator import Paginator


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

        pending_approvals_count = Match.objects.filter(
            request_session__student=current_user,  
            tutor_approved=False  
        ).count()

        matched_requests_count = Match.objects.filter(request_session__student=current_user, tutor_approved=True).count()

        context.update(get_calendar_context(current_user))
        context.update({
            'unmatched_student_requests': unmatched_student_requests,
            'is_student_view': True,
            'matched_requests_count': matched_requests_count,
            'pending_approvals_count': pending_approvals_count,
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
            'days': [day.get_day_of_week_display() for day in match.request_session.days.all()]
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
def update_tutor_subject(request, subject_id):
    current_user = request.user
    if not current_user.is_tutor:
        return redirect('dashboard')
    
    # Get the TutorSubject object based on the current user and subject_id
    tutor_subject = get_object_or_404(TutorSubject, tutor=current_user, id=subject_id)

    # Handle the form submission
    if request.method == 'POST':
        form = UpdateProficiencyForm(request.POST, instance=tutor_subject)
        if form.is_valid():
            form.save()  # Only update the proficiency field
            messages.success(request, 'Proficiency level updated successfully!')
            return redirect('view_all_tutor_subjects')
        else:
            messages.error(request, 'There was an error updating your proficiency. Please try again.')

    # If GET request, display form with the current proficiency
    else:
        form = UpdateProficiencyForm(instance=tutor_subject)

    context = {
        'form': form,
        'tutor_subject': tutor_subject,
    }

    return render(request, 'update_tutor_subject.html', context)


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
def student_view_unmatched_requests(request):
    """Display unmatched requests for the logged-in student."""
    current_user = request.user

    # Ensure the user is a student
    if not current_user.is_student:
        return redirect('dashboard')  # Redirect non-students to their dashboard

    unmatched_requests = RequestSession.objects.filter(
        student=current_user,
        match__isnull=True
    ).prefetch_related('days')

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
        # Pass the logged-in student to the form
        form = RequestSessionForm(request.POST, student=request.user)
        if form.is_valid():
            try:
                # Create the RequestSession object but don't save it yet
                new_request = form.save(commit=False)
                # Set additional fields
                new_request.student = request.user  # Assign the logged-in student
                new_request.date_requested = now().date()  # Set the current date
                new_request.save()  # Save the RequestSession

                # Handle selected days for the session
                days_selected = request.POST.getlist('days')  # Get the selected days from the form
                for day in days_selected:
                    RequestSessionDay.objects.create(
                        request_session=new_request,
                        day_of_week=day
                    )

                # Redirect to a success page or the student's unmatched requests
                return redirect('student_view_unmatched_requests')
            except IntegrityError:
                # Handle duplicate request error
                messages.error(request, "You have already submitted a request for this subject.")
    else:
        # Pass the logged-in student to the form for initialization
        form = RequestSessionForm(student=request.user)

    return render(request, 'student_submits_request.html', {'form': form})

@login_required
def delete_request(request, request_id):
    """Delete a request session for the logged-in student."""
    try:
        unmatched_request = RequestSession.objects.get(id=request_id, student=request.user, match__isnull=True)
        unmatched_request.delete()
        messages.success(request, "Request deleted successfully.")
    except RequestSession.DoesNotExist:
        messages.error(request, "Request not found or you do not have permission to delete it.")
    
    return redirect('student_view_unmatched_requests')


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

def is_request_late(request_date):
    """Check if a request was made after the academic year started."""
    term_dates = [
            (date(request_date.year, 9, 1), date(request_date.year, 12, 20)),  # Autumn
            (date(request_date.year + 1, 1, 4), date(request_date.year + 1, 3, 31)),  # Spring
            (date(request_date.year + 1, 4, 15), date(request_date.year + 1, 7, 20))  # Summer
        ]
    
    for term_start, _ in term_dates:
        if request_date >= term_start - timedelta(weeks=2) and request_date <= term_start:
            return True
        
    return False

@login_required
def admin_requested_sessions(request):
    if not request.user.is_admin:
        return redirect('dashboard')

    # Get unmatched requests
    requests = RequestSession.objects.filter(match__isnull=True)
    
    # Handle search
    search_query = request.GET.get('search', '').lower()
    if search_query:
        requests = requests.filter(
            Q(student__username__icontains=search_query) |
            Q(subject__name__icontains=search_query) |
            Q(proficiency__icontains=search_query)
        )

    # Add pagination - 6 items per page
    paginator = Paginator(requests, 6)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)
    
    # Create forms for each request
    requests_with_forms = []
    for req in requests_page:
        requests_with_forms.append({
            'request': req,
            'form': TutorMatchForm(req),
            'is_late': is_request_late(req.date_requested)
        })

    return render(request, 'admin_requested_sessions.html', {
        'requests_with_forms': requests_with_forms,
        'page_obj': requests_page,
        'is_admin_view': True,
        'search_query': search_query
    })

@login_required
def pending_approvals(request):
    """List pending matches for tutors or admins."""
    current_user = request.user

    if current_user.is_admin:
        # Admin: See all pending requests
        matches = Match.objects.filter(tutor_approved=False)
        can_approve = False  
    elif current_user.is_tutor:
        # Tutor: See only their pending requests
        matches = Match.objects.filter(tutor=current_user, tutor_approved=False)
        can_approve = True 
    elif current_user.is_student:
        # Student: See only their own pending requests
        matches = Match.objects.filter(request_session__student=current_user, tutor_approved=False)
        can_approve = False 
    else:
        return redirect('dashboard')
