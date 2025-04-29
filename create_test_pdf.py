from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def create_test_pdf(output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add some sample transactions
    transactions = [
        ("Woolworths", "50.00", "Groceries"),
        ("Coles", "35.50", "Groceries"),
        ("Shell", "45.00", "Fuel"),
        ("Netflix", "15.99", "Entertainment"),
        ("Spotify", "12.99", "Entertainment")
    ]
    
    # Add header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Sample Credit Card Statement")
    
    # Add transaction table
    c.setFont("Helvetica", 12)
    y = height - 2*inch
    for merchant, amount, category in transactions:
        c.drawString(1*inch, y, f"{merchant}: ${amount} ({category})")
        y -= 0.3*inch
    
    c.save()

if __name__ == "__main__":
    create_test_pdf("input/sample.pdf") 