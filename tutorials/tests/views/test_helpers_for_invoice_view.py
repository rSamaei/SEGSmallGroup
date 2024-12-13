from django.test import TestCase
from tutorials.helpers import InvoiceService
from django.core.exceptions import ObjectDoesNotExist
from unittest.mock import patch
from tutorials.models import User, Subject, RequestSession, Match, TutorSubject, Invoice

class InvoiceServiceTester(TestCase):
    """Class to test invoice service."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/request_session.json',
        'tutorials/tests/fixtures/tutor_subjects.json',
    ]

    def setUp(self):
        self.student = User.objects.filter(user_type='student').first()
        self.tutor = User.objects.filter(user_type='tutor').first()
        self.subject = Subject.objects.first()
        self.tutor_subject = TutorSubject.objects.first()
        self.request_session = RequestSession.objects.first()
        
        self.match = Match.objects.create(
            tutor=self.tutor,
            request_session=self.request_session,
            tutor_approved=True
        )

    def test_get_user_invoices_paid(self):
        """Test getting paid invoices"""
        invoice = Invoice.objects.create(
            match=self.match,
            payment=25.00,
            payment_status='paid'
        )
        
        paid, unpaid = InvoiceService.get_user_invoices([self.match])
        
        self.assertEqual(len(paid), 1)
        self.assertEqual(len(unpaid), 0)
        self.assertEqual(paid[0], invoice)

    def test_get_user_invoices_waiting(self):
        """Test getting waiting invoices"""
        invoice = Invoice.objects.create(
            match=self.match,
            payment=25.00,
            payment_status='waiting'
        )
        
        paid, unpaid = InvoiceService.get_user_invoices([self.match])
        
        self.assertEqual(len(paid), 1)
        self.assertEqual(len(unpaid), 0)
        self.assertEqual(paid[0], invoice)

    def test_get_user_invoices_unpaid(self):
        """Test getting unpaid invoices"""
        invoice = Invoice.objects.create(
            match=self.match,
            payment=25.00,
            payment_status='unpaid'
        )
        
        paid, unpaid = InvoiceService.get_user_invoices([self.match])
        
        self.assertEqual(len(paid), 0)
        self.assertEqual(len(unpaid), 1)
        self.assertEqual(unpaid[0], invoice)

    # @patch('tutorials.helpers.PDFUser')
    # def test_generate_pdf(self, mock_pdf_user):
    #     """Test PDF generation"""
    #     invoice = Invoice.objects.create(
    #         match=self.match,
    #         payment=25.00,
    #         payment_status='unpaid'
    #     )

    #     print(TutorSubject.objects.get(
    #         tutor=self.match.tutor,
    #         subject=self.request_session.subject
    #     ))
        
    #     # Set up mock return value
    #     mock_pdf_user.generatePDF.return_value = 'path/to/pdf'
        
    #     pdf_path = InvoiceService.generate_pdf(self.student, self.match, invoice)
        
    #     # Verify PDF generation was called with correct parameters
    #     mock_pdf_user.generatePDF.assert_called_once_with(
    #         f"{self.student.first_name} {self.student.last_name}",
    #         f"{self.tutor.first_name} {self.tutor.last_name}",
    #         self.tutor_subject.price,
    #         self.request_session.frequency,
    #         invoice.payment,
    #         self.subject.name,
    #         self.request_session.get_frequency_display(),
    #         self.request_session.proficiency,
    #         invoice.bank_transfer
    #     )
        
    #     self.assertEqual(pdf_path, 'path/to/pdf')

    def test_generate_pdf_no_tutor_subject(self):
        """Test PDF generation fails when tutor subject doesn't exist"""
        invoice = Invoice.objects.create(
            match=self.match,
            payment=25.00
        )
        
        # Delete tutor subject to force error
        self.tutor_subject.delete()
        
        with self.assertRaises(ObjectDoesNotExist):
            InvoiceService.generate_pdf(self.student, self.match, invoice)