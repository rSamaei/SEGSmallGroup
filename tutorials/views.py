from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, RequestSessionForm
from tutorials.helpers import login_prohibited

from tutorials.models import RequestSession
from django.apps import apps
from .models import RequestSession
from .forms import RequestSessionForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView



@login_required
def dashboard(request):
    # Display the current user's dashboard.
    current_user = request.user
    
    # Determine which requests to show based on the user type
    if current_user.user_type == 'admin':
        # Admins can see all requests
        sessions = RequestSession.objects.all()
    elif current_user.user_type == 'tutor':
        # Tutors can see only the requests where they are assigned as the tutor
        sessions = RequestSession.objects.filter(tutor=current_user)
    else:
        # Students can only see their own requests
        sessions = RequestSession.objects.filter(student=current_user)
    
    noRequestMessage = ''
    if not sessions:
        noRequestMessage = 'No requests were found'
    
    return render(request, 'dashboard.html', {
        'user': current_user,
        'requests': sessions, 
        'message': noRequestMessage
    })
        
@login_prohibited
def home(request):
    #Display the application's start/home screen.

    return render(request, 'home.html')


class AddRequestView(LoginRequiredMixin, CreateView):
    model = RequestSession
    form_class = RequestSessionForm
    template_name = 'add_request.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        # Automatically set the current user as the student
        form.instance.student = self.request.user
        # Optionally, set the tutor as None or based on some other logic
        form.instance.tutor = None  # You can keep it as None or apply logic to assign a tutor
        return super().form_valid(form)

@login_required
def delete_request(request, request_id):
    # Get the request session object to delete
    request_session = get_object_or_404(RequestSession, id=request_id)
    
    # Check if the logged-in user is the owner of the request (or an admin)
    if request.user == request_session.student or request.user.user_type == 'admin':
        if not request_session.tutor:
            request_session.delete()  # Delete the request if no tutor is assigned
            messages.success(request, "Your request has been deleted.")
        else:
            messages.error(request, "You cannot delete a request with a tutor assigned.")
    else:
        messages.error(request, "You do not have permission to delete this request.")
    
    return redirect('dashboard')


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
    #Display login screen and handle user login.

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        #Display log in template.

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        #Handle log in attempt.

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        #Render log in template with blank log in form.

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    #Log out the current user

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    #Display password change screen and handle password change requests.

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        #Pass the current user to the password change form.

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        #Handle valid form by saving the new password.

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        #Redirect the user after successful password change.

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    #Display user profile editing screen, and handle profile modifications.

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        #Return the object (user) to be updated.
        user = self.request.user
        return user

    def get_success_url(self):
        #Return redirect URL after successful update.
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    #Display the sign up screen and handle sign ups.

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)
