from django.core.management.base import BaseCommand, CommandError
from datetime import date, timedelta

from tutorials.models import User, Subject, RequestSession, Match, TutorSubject, RequestSessionDay, Invoice

import pytz
from faker import Faker
from random import randint, choice, sample

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'user_type': 'admin'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe', 'user_type': 'tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson', 'user_type': 'student'},
]

subject_names = [
    'Discrete Maths', 'Machine Learning', 'C++', 'Python', 'Java', 
    'SQL', 'Neural Networks', 'Assembly', 'Rust', 'C'
]

request_session_fixtures = [
    {
        'student': '@charlie',
        'subject': 'Python',
        'proficiency': 'Beginner',
        'frequency': 1.0,
        'date_requested': date(2024, 8, 20)
    },
    {
        'student': '@charlie',
        'subject': 'Java',
        'proficiency': 'Intermediate',
        'frequency': 2.0,
        'date_requested': date(2024, 10, 10)
    },
    {
        'student': '@charlie',
        'subject': 'SQL',
        'proficiency': 'Advanced',
        'frequency': 0.5,
        'date_requested': date(2025, 1, 7)
    }
]

request_session_days_fixtures = [
    [
        {
            'request_session': {
                'student': '@charlie',
                'subject': 'Python'
            },
            'day_of_week': 'Monday'
        },
        {
            'request_session': {
                'student': '@charlie',
                'subject': 'Java'
            },
            'day_of_week': 'Wednesday, Thursday'
        },
        {
            'request_session': {
                'student': '@charlie',
                'subject': 'SQL'
            },
            'day_of_week': 'Friday'
        }
    ]
]

TutorSubject_fixtures = [
    {
        'tutor': '@janedoe',
        'subject': 'Python',
        'proficiency': 'Advanced'
    },
    {
        'tutor': '@janedoe',
        'subject': 'Java',
        'proficiency': 'Intermediate'
    },
    {
        'tutor': '@janedoe',
        'subject': 'SQL',
        'proficiency': 'Advanced'
    }
]

match_fixtures = [
    {
        'tutor': '@janedoe',
        'request_session': {
            'student': '@charlie',
            'subject': 'Python'
        },
        'tutor_approved': True
    },
    {
        'tutor': '@janedoe',
        'request_session': {
            'student': '@charlie',
            'subject': 'Java'
        },
        'tutor_approved': False
    }
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 600
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    # def __init__(self):
    #     self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.faker = Faker('en_GB')
        self.create_users()
        self.users = User.objects.all()
        self.create_subjects()
        self.create_fixture_request_sessions()
        self.create_request_sessions()
        self.create_tutor_subjects()
        self.create_fixture_matches()
        self.create_matches()
        self.create_invoices()

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

    def create_fixture_request_sessions(self):
        for req in request_session_fixtures:
            student = User.objects.get(username=req['student'])
            subject = Subject.objects.get(name=req['subject'])
            request_session = RequestSession.objects.create(
                student=student,
                subject=subject,
                proficiency=req['proficiency'],
                frequency=req['frequency'],
                date_requested=req['date_requested']
            )
            if req['frequency'] == 0.5 or req['frequency'] == 1.0:
                day = choice(DAYS_OF_WEEK)
                RequestSessionDay.objects.create(
                    request_session=request_session,
                    day_of_week=day
                )
            elif req['frequency'] == 2.0:
                days = sample(DAYS_OF_WEEK, k=2)
                for day in days:
                    RequestSessionDay.objects.create(
                        request_session=request_session,
                        day_of_week=day
                    )

    def create_request_sessions(self):
        students = User.objects.filter(user_type='student')
        subjects = Subject.objects.all()
        
        year = date.today().year - 1 if date.today().month >= 1 and date.today().month < 9 else date.today().year
        start = date(year, 7, 1)
        possible_dates = [start + timedelta(days=x) for x in range(180)]

        for student in students:    # create a request session for each student in the database
            for _ in range(randint(1, 3)):  # fill the database with each student requesting 1 to 3 subjects
                subject = choice(subjects)
                proficiency = choice(['Beginner', 'Intermediate', 'Advanced'])
                frequency = choice([0.5, 1.0, 2.0])
                session_date = choice(possible_dates)  # Randomly pick a date
                try:
                    request_session, created = RequestSession.objects.get_or_create(
                        student=student,
                        subject=subject,
                        defaults={
                            'proficiency': proficiency, 
                            'frequency': frequency,
                            'date_requested': session_date  # Add the date
                        }
                    )
                    if created:
                        if frequency == 0.5 or frequency == 1.0:  # Fortnightly / Weekly
                            day = choice(DAYS_OF_WEEK)
                            RequestSessionDay.objects.create(
                                request_session=request_session,
                                day_of_week=day
                            )
                        elif frequency == 2.0:  # Biweekly
                            days = sample(DAYS_OF_WEEK, k=2)  # Select two different days
                            for day in days:
                                RequestSessionDay.objects.create(
                                    request_session=request_session,
                                    day_of_week=day
                                )
                except Exception as e:
                    print(f"Error creating request session: {e}")
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

    def create_fixture_matches(self):
        for match in match_fixtures:
            tutor = User.objects.get(username=match['tutor'])
            request = RequestSession.objects.get(
                student__username=match['request_session']['student'],
                subject__name=match['request_session']['subject']
            )
            Match.objects.create(
                tutor=tutor,
                request_session=request,
                tutor_approved=match['tutor_approved']
            )

    def create_matches(self):
        sessions = list(RequestSession.objects.all())
        half_sessions = len(sessions) // 2
        selected_sessions = self.faker.random_elements(elements=sessions, length=half_sessions, unique=True)

        for session in selected_sessions:
            try:
                tutors = User.objects.filter(user_type='tutor')  # get all tutors by filtering users
                tutors_for_subject = tutors.filter(
                    tutor_subjects__subject=session.subject  # filter tutors if the subject of the requested session appears in tutor subjects table indicating the tutor can teach that session
                )

                # if there are tutors available for this subject, match one to the session
                if tutors_for_subject.exists():
                    tutor = choice(tutors_for_subject)  # randomly choose a tutor
                    Match.objects.get_or_create(
                        request_session=session,
                        tutor=tutor,
                        defaults={'tutor_approved': choice([True, False])}  # Randomly set tutor_approved
                    )
                else:
                    print(f"No tutor available for subject: {session.subject.name}")
            except Exception as e:
                print(f"Error creating match for session {session.id}: {e}")

        print("Matches seeded.")

    def create_invoices(self):
        fake = Faker()
        matches = Match.objects.filter(tutor_approved=True)
        
        for session_match in matches:
            # Calculate random price between 20 and 100
            tempPrice = randint(20, 100)
            # Randomly choose payment status
            payment_status = choice(['paid', 'waiting', 'unpaid'])
            
            # Create invoice with conditional bank transfer
            tempInvoice = Invoice.objects.create(
                match=session_match,
                payment=tempPrice,
                payment_status=payment_status,
                bank_transfer=fake.iban() if payment_status == 'paid' else None
            )
            
        print("Invoices seeded.")
            

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}@example.org"