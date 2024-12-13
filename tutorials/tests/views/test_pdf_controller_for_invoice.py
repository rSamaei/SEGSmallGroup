from django.test import TestCase
from unittest.mock import patch, mock_open, MagicMock
from PyPDF2 import PdfReader
from tutorials.pdfController import PDFUser

class TestPDFController(TestCase):
    """Test PDF controller functions"""

    def setUp(self):
        self.test_data = {
            'student': 'John Doe',
            'tutor': 'Jane Smith',
            'price1': '25.00',
            'price2': '50.00',
            'price3': '75.00',
            'subject': 'Mathematics',
            'freq': 'Weekly',
            'prof': 'Advanced',
            'bank_transfer': 'GB12BANK12345612345678'
        }

    def test_create_overlay_with_bank_transfer(self):
        """Test creating overlay PDF with bank transfer"""
        overlay = PDFUser.createOverlay(**self.test_data)
        self.assertIsInstance(overlay, PdfReader)
        self.assertEqual(len(overlay.pages), 1)

    def test_create_overlay_without_bank_transfer(self):
        """Test creating overlay PDF without bank transfer"""
        self.test_data['bank_transfer'] = ''
        overlay = PDFUser.createOverlay(**self.test_data)
        self.assertIsInstance(overlay, PdfReader)
        self.assertEqual(len(overlay.pages), 1)

    @patch('tutorials.pdfController.PdfReader')
    @patch('tutorials.pdfController.PdfWriter')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_pdf_success(self, mock_file, mock_writer, mock_reader):
        """Test successful PDF generation"""
        mock_reader.return_value.pages = [MagicMock()]
        
        result = PDFUser.generatePDF(**self.test_data)
        
        mock_file.assert_called()
        mock_writer.return_value.write.assert_called_once()
        self.assertIn('tempInvoice_', result)
        self.assertIn('.pdf', result)

    @patch('tutorials.pdfController.PdfReader')
    def test_generate_pdf_file_not_found(self, mock_reader):
        """Test PDF generation with missing base template"""
        mock_reader.side_effect = FileNotFoundError()
        
        with self.assertRaises(Exception) as context:
            PDFUser.generatePDF(**self.test_data)
        
        self.assertIn('Base invoice template not found', str(context.exception))

    @patch('tutorials.pdfController.PdfReader')
    def test_generate_pdf_general_error(self, mock_reader):
        """Test PDF generation with general error"""
        mock_reader.side_effect = Exception('Test error')
        
        with self.assertRaises(Exception) as context:
            PDFUser.generatePDF(**self.test_data)
        
        self.assertIn('An error occurred while generating the PDF', str(context.exception))

    def test_bank_transfer_format(self):
        """Test bank transfer number formatting in overlay"""
        overlay = PDFUser.createOverlay(**self.test_data)
        self.assertIsInstance(overlay, PdfReader)

        self.test_data['bank_transfer'] = None
        overlay = PDFUser.createOverlay(**self.test_data)
        self.assertIsInstance(overlay, PdfReader)

        self.test_data['bank_transfer'] = '   '
        overlay = PDFUser.createOverlay(**self.test_data)
        self.assertIsInstance(overlay, PdfReader)