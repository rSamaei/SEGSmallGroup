"""Unit tests for the Subject model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tutorials.models import Subject

class SubjectModelTestCase(TestCase):  # Fixed class name
    """Unit tests for the Subject model."""

    fixtures = [
        'tutorials/tests/fixtures/subjects.json',
    ]

    def setUp(self):
        self.subject = Subject.objects.get(name='Mathematics')

    def test_subject_name_must_be_unique(self):
        subject = Subject(name='Mathematics')  
        with self.assertRaises(ValidationError):
            subject.full_clean()
    
    def test_can_get_all_subjects(self):
        subjects = Subject.objects.all()
        self.assertEqual(len(subjects), 9)
    
    def test_subject_str_method(self):
        self.assertEqual(str(self.subject), 'Mathematics')

    def test_subject_name_cannot_be_blank(self):
        self.subject.name = ''
        with self.assertRaises(ValidationError):
            self.subject.full_clean()

    def test_subject_name_can_be_20_characters(self):
        self.subject.name = 'x' * 20
        try:
            self.subject.full_clean()
        except ValidationError:
            self.fail("Subject name of 50 characters raised ValidationError")

    def test_subject_name_cannot_exceed_20_characters(self):
        self.subject.name = 'x' * 21
        with self.assertRaises(ValidationError):
            self.subject.full_clean()

    def test_can_create_subject(self):
        subject = Subject(name='New Subject')
        try:
            subject.full_clean()
            subject.save()
        except ValidationError:
            self.fail("Could not create valid subject")
        self.assertEqual(Subject.objects.filter(name='New Subject').count(), 1)

    def test_can_delete_subject(self):
        initial_count = Subject.objects.count()
        self.subject.delete()
        self.assertEqual(Subject.objects.count(), initial_count - 1)

    def test_can_update_subject(self):
        self.subject.name = 'Updated Mathematics'
        try:
            self.subject.full_clean()
            self.subject.save()
        except ValidationError:
            self.fail("Could not update subject")
        self.assertEqual(Subject.objects.get(id=self.subject.id).name, 'Updated Mathematics')