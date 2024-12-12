from django.conf import settings
from django.shortcuts import redirect

from tutorials.pdfController import PDFUser
from .models import Invoice, TutorSubject

def login_prohibited(view_function):
    """Decorator for view functions that redirect users away if they are logged in."""
    
    def modified_view_function(request):
        if request.user.is_authenticated:
            return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN)
        else:
            return view_function(request)
    return modified_view_function

class InvoiceService:
    @staticmethod
    def get_user_invoices(matches):
        paid = []
        unpaid = []
        for match in matches:
            invoice = Invoice.objects.filter(match=match).first()
            if invoice:
                if invoice.payment_status == 'paid' or invoice.payment_status == 'waiting':
                    paid.append(invoice)
                else:
                    unpaid.append(invoice)
        return paid, unpaid

    @staticmethod
    def generate_pdf(user, match, invoice):
        tutor = match.tutor
        tutor_name = f"{tutor.first_name} {tutor.last_name}"
        request_session = match.request_session
        tutor_subject = TutorSubject.objects.get(
            tutor=tutor,
            subject=request_session.subject
        )
        
        student_name = f"{user.first_name} {user.last_name}"
        PDFUser.generatePDF(
            student_name, tutor_name, tutor_subject.price,
            request_session.frequency, invoice.payment,
            request_session.subject.name,
            request_session.get_frequency_display(),
            request_session.proficiency,
            invoice.bank_transfer
        )