from django.core.management.base import BaseCommand
from tutorials.models import User, RequestSession, Subject
from faker import Faker
from random import randint, choice

class Command(BaseCommand):
    """Build automation command to seed the database."""
    USER_COUNT = 300
    REQUEST_COUNT = 100
    SUBJECT_COUNT = 10
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')
        super().__init__()

    def handle(self, *args, **options):
        self.create_subjects()
        self.subjects = Subject.objects.all()

        self.create_users()
        self.users = User.objects.all()

        self.create_requests()

    def create_subjects(self):
        subject_names = [
            "Mathematics", "Physics", "Chemistry", "Biology",
            "English", "History", "Computer Science", "Art",
            "Music", "Physical Education"
        ]
        
        print("Seeding subjects...")
        for name in subject_names:
            try:
                Subject.objects.get_or_create(name=name)
            except Exception as e:
                print(f"Error creating subject {name}: {e}")
        
        self.subjects = Subject.objects.all()
        print(f"Subject seeding complete. Total: {self.subjects.count()}")

    def create_users(self):
        print("Seeding users...")
        self.generate_user_fixtures()
        self.generate_random_users()
        print("User seeding complete.")

    def generate_user_fixtures(self):
        user_fixtures = [
            {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'user_type': 'student'},
            {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe', 'user_type': 'tutor'},
            {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson', 'user_type': 'admin'},
        ]
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        while User.objects.count() < self.USER_COUNT:
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            self.try_create_user({
                'username': self.create_username(first_name, last_name),
                'email': self.create_email(first_name, last_name),
                'first_name': first_name,
                'last_name': last_name,
                'user_type': self.random_user_type(),
            })

    def try_create_user(self, data):
        try:
            User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=self.DEFAULT_PASSWORD,
                first_name=data['first_name'],
                last_name=data['last_name'],
                user_type=data['user_type'],
            )
        except Exception as e:
            print(f"Error creating user: {e}")

    def create_requests(self):
        print("Seeding requests...")
        students = User.objects.filter(user_type='student')
        for _ in range(self.REQUEST_COUNT):
            student = choice(students)
            subject = choice(self.subjects)
            frequency = choice([1, 0.5, 2, 0.25])  # Weekly, Fortnightly, Bi-weekly, Monthly
            proficiency = choice(['beginner', 'intermediate', 'advanced'])

            # Create RequestSession without assigning a tutor
            try:
                RequestSession.objects.create(
                    student=student,
                    subject=subject,
                    frequency=frequency,
                    proficiency=proficiency,
                    tutor=None  # Explicitly set no tutor
                )
            except Exception as e:
                print(f"Error creating request: {e}")

        print(f"Request seeding complete. Total: {RequestSession.objects.count()}")


    def create_username(self, first_name, last_name):
        return f"@{first_name.lower()}{last_name.lower()}"

    def create_email(self, first_name, last_name):
        return f"{first_name.lower()}.{last_name.lower()}@example.org"

    def random_user_type(self):
        return choice(['student', 'tutor', 'admin'])
