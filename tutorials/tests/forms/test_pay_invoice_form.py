from django.test import TestCase
from tutorials.forms import PayInvoice

class PayInvoiceTest(TestCase):
    def test_valid_data(self):
        form = PayInvoice(data={
            "bank_transfer": "GB12BANK12345612345678",
            "session": 1,
        })
        self.assertTrue(form.is_valid())

    def test_missing_bank_transfer(self):
        form = PayInvoice(data={
            "bank_transfer": "",
            "session": 1,
        })
        self.assertFalse(form.is_valid())
