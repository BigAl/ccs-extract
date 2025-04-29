from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from datetime import datetime

def create_test_pdf(output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add some sample transactions in the correct format
    transactions = [
        ("15 Apr 2025", "50.00", "WOOLWORTHS SUPERMARKET"),
        ("14 Apr 2025", "35.50", "COLES SUPERMARKET"),
        ("13 Apr 2025", "45.00", "SHELL COLES EXPRESS"),
        ("12 Apr 2025", "15.99", "NETFLIX SUBSCRIPTION"),
        ("11 Apr 2025", "12.99", "SPOTIFY PREMIUM")
    ]
    
    # Add header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Sample Credit Card Statement")
    
    # Add transaction table
    c.setFont("Helvetica", 12)
    y = height - 2*inch
    for date, amount, merchant in transactions:
        c.drawString(1*inch, y, f"{date} ${amount} {merchant}")
        y -= 0.3*inch
    
    c.save()

if __name__ == "__main__":
    create_test_pdf("input/sample.pdf") 