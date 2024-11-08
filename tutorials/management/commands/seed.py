from django.core.management.base import BaseCommand, CommandError

from tutorials.models import User, Subject, RequestSession, Match, TutorSubject

import pytz
from faker import Faker
from random import randint, random

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson'},
]

subject_names = [
    'Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 
    'History', 'Computer Science', 'Art', 'Music', 'Physical Education'
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        # self.create_subjects()
        # self.create_request_sessions()
        # self.create_tutor_subjects()
        # self.create_matches()

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
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )

    # def create_subjects(self):
    #     for name in subject_names:
    #         Subject.objects.get_or_create(name=name)
    #     print("Subjects seeded.")

    # def create_request_sessions(self):
    #     students = User.objects.filter(user_type='student')
    #     subjects = Subject.objects.all()

    #     for student in students:
    #         for _ in range(randint(1, 3)):  # Each student can request between 1 to 3 sessions
    #             subject = choice(subjects)
    #             proficiency = choice(['Beginner', 'Intermediate', 'Advanced'])
    #             frequency = randint(1, 5)

    #             RequestSession.objects.get_or_create(
    #                 student=student,
    #                 subject=subject,
    #                 defaults={'proficiency': proficiency, 'frequency': frequency}
    #             )
    #     print("Request sessions seeded.")

    # def create_tutor_subjects(self):
    #     tutors = User.objects.filter(user_type='tutor')
    #     subjects = Subject.objects.all()

    #     for tutor in tutors:
    #         for _ in range(randint(1, 5)):  # Each tutor can teach between 1 to 5 subjects
    #             subject = choice(subjects)
    #             proficiency_level = choice(['Intermediate', 'Advanced', 'Expert'])

    #             TutorSubject.objects.get_or_create(
    #                 tutor=tutor,
    #                 subject=subject,
    #                 defaults={'proficiency_level': proficiency_level}
    #             )
    #     print("Tutor subjects seeded.")

    # def create_matches(self):
    #     sessions = RequestSession.objects.all()
    #     tutors = User.objects.filter(user_type='tutor')

    #     for session in sessions:
    #         tutor = choice(tutors)
    #         Match.objects.get_or_create(
    #             request_session=session,
    #             tutor=tutor
    #         )
    #     print("Matches seeded.")

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}@example.org"
