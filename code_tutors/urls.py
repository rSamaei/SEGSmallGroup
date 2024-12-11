"""
URL configuration for code_tutors project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from tutorials import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/', views.admin_requested_sessions, name='admin_requested_sessions'),
    path('requests/<int:request_id>/', views.admin_requested_session_highlighted, name='admin_requested_session_highlighted'),
    path('match/<int:request_id>/', views.create_match, name='create_match'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('registerAdmin/',views.registerNewAdmin, name='registerAdmin'),
    path('update_tutor_subject/<int:subject_id>/', views.update_tutor_subject, name='update_tutor_subject'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('reject_match/<int:match_id>/', views.reject_match, name='reject_match'),

    path('view_all_users/', views.view_all_users, name='view_all_users'),
    path('view_all_tutor_subjects/', views.view_all_tutor_subjects, name='view_all_tutor_subjects'),
    path('student/unmatched-requests/', views.student_view_unmatched_requests, name='student_view_unmatched_requests'),
    path('add-new-subject/', views.add_new_subject, name='add_new_subject'),
    path('view_matched_requests/', views.view_matched_requests, name='view_matched_requests'),
    path('delete_tutor_subject/<int:subject_id>/', views.delete_tutor_subject, name='delete_tutor_subject'),

    path('submit-request/', views.student_submits_request, name='student_submits_request'),
    path('delete-request/<int:request_id>/', views.delete_request, name='delete_request'),


    path('invoice/',views.invoice, name='invoice'),

    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('approve-match/<int:match_id>/', views.approve_match, name='approve_match'),
    

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)