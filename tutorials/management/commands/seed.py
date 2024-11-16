from django.core.management.base import BaseCommand, CommandError

from tutorials.models import User, Subject, RequestSession, Match, TutorSubject

import pytz
from faker import Faker
from random import randint, choice

# addded user_type to these
user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'user_type': 'admin'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe', 'user_type': 'tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson', 'user_type': 'student'},
]

# for subject data
subject_names = [
    'Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 
    'History', 'Computer Science', 'Art', 'Music', 'Physical Education'
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 600
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        self.create_subjects()
        self.create_request_sessions()
        self.create_tutor_subjects()
        self.create_matches()

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        user_type = choice(['student', 'tutor', 'admin'])  # randomly assign a user type
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name, 'user_type': user_type})
       
    def try_create_user(self, data):
        try:
            self.create_user(data)
        except Exception as e:
            print(f"Error creating user: {e}")

    def create_user(self, data):
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
            user_type=data['user_type'],
        )
    
    def create_subjects(self):
        for name in subject_names:
            Subject.objects.get_or_create(name=name)
        print("Subjects seeded.")

    def create_request_sessions(self):
        students = User.objects.filter(user_type='student')
        subjects = Subject.objects.all()

        for student in students:    # create a request session for each student in the database
            for _ in range(randint(1, 3)):  # fill the database with each student requesting 1 to 3 subjects
                subject = choice(subjects)
                proficiency = choice(['Beginner', 'Intermediate', 'Advanced'])
                frequency = randint(1, 5)
                # if the student requesting that subject hasn't already been generated create it 
                RequestSession.objects.get_or_create(
                    student=student,
                    subject=subject,
                    defaults={'proficiency': proficiency, 'frequency': frequency}
                )
        print("Request sessions seeded.")

    def create_tutor_subjects(self):
        tutors = User.objects.filter(user_type='tutor')
        subjects = Subject.objects.all()

        for tutor in tutors:    # similarly for every tutor in the database create data for them
            for _ in range(randint(1, 5)):  # fill the database with each tutor being able to teach 1-5 subjects
                subject = choice(subjects)
                proficiency = choice(['Beginner', 'Intermediate', 'Advanced'])
                # if the tutor teaching that subject hasn't already been generated create it 
                TutorSubject.objects.get_or_create(
                    tutor=tutor,
                    subject=subject,
                    defaults={'proficiency': proficiency}
                )
        print("Tutor subjects seeded.")

    def create_matches(self):
        sessions = list(RequestSession.objects.all())
        half_sessions = len(sessions) // 2
        selected_sessions = self.faker.random_elements(elements=sessions, length=half_sessions, unique=True)

        for session in selected_sessions:
            tutors = User.objects.filter(user_type='tutor')     # get all tutors by filtering users
            tutors_for_subject = tutors.filter(
                tutor_subjects__subject=session.subject # filter tutors if the subject of the requested session appears in tutor subjects table indicating the tutor can teach that session
            )

            # if there are tutors available for this subject, match one to the session
            if tutors_for_subject.exists():
                tutor = choice(tutors_for_subject)  # randomly choose a tutor
                Match.objects.get_or_create(
                    request_session=session,
                    tutor=tutor
                )
            else:
                print(f"No tutor available for subject: {session.subject.name}")

        print("Matches seeded.")

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}@example.org"
