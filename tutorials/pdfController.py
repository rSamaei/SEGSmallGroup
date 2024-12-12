from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from reportlab.pdfgen import canvas

class PDFUser():
    
    
    #Billed to: 57, 600
    #From: 375, 600
    #Price1: 475, 412
    #Price2: 475, 378
    #Price3: 460, 348
    #Lesson: 57, 445

    def createOverlay(student, tutor, price1, price2, price3, subject, freq, prof, bank_transfer):
        packet = BytesIO()
        can = canvas.Canvas(packet)
        can.drawString(57,600,student)
        can.drawString(375,600,tutor)
        can.drawString(475,412,price1)
        can.drawString(475,378,price2)
        can.drawString(460,348,price3)
        can.drawString(57,445,subject)
        can.drawString(57,425,freq)
        can.drawString(57,405,prof)
        if bank_transfer and bank_transfer.strip():
            can.drawString(57,385,"Bank Transfer: " + bank_transfer)
        else:
            can.drawString(57,385,"Bank Transfer: Pending")
            
        can.save()
        packet.seek(0)
        return PdfReader(packet)
    

    def generatePDF(student, tutor, price1, price2, price3, subject, freq, prof, bank_transfer):
        path = "static/BaseInvoice.pdf"
        input_pdf = PdfReader(path)
        writer = PdfWriter()
        overlay = PDFUser.createOverlay(student, tutor, str(price1), str(price2), str(price3), 
                                  subject, freq, prof, bank_transfer)
        for page_number, page in enumerate(input_pdf.pages):
            if page_number == 0:
                page.merge_page(overlay.pages[0])
            writer.add_page(page)

        with open("static/tempInvoice.pdf", "wb") as output_file:
            writer.write(output_file)
