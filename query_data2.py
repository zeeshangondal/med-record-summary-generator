import argparse
from langchain_community.llms.ollama import Ollama
import os
from PyPDF2 import PdfReader

from fpdf import FPDF


def get_pdf_filenames(directory):
    return [file for file in os.listdir(directory) if file.endswith('.pdf')]

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from the given PDF file.
    
    :param pdf_path: Path to the PDF file.
    :return: Extracted text as a string.
    """
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
        return text

def generate_pdf_table(rows, output_pdf="output.pdf"):
    # Define headers
    headers = ["Visited Date", "Diagnosis/Prognosis", "Record Reference"]
    
    # Split the response text into rows based on newlines
    
    # Initialize PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Set font and size
    pdf.set_font("Arial", size=7)
    
    # Add headers
    for header in headers:
        pdf.cell(63, 10, header, border=1)
    pdf.ln(10)
    
    # Process each row
    for row in rows:
        # Initialize empty cells
        visited_date = row[0]
        diagnosis_prognosis = [1]
        record_reference = [2]
        
        # Add row data to the table
        pdf.cell(63, 10, visited_date, border=1)
        pdf.cell(63, 10, diagnosis_prognosis, border=1)
        pdf.cell(63, 10, record_reference, border=1)
        pdf.ln(10)

    # Output the PDF
    pdf.output(output_pdf)




from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_pdf(data, filename="output.pdf"):
    # Create a PDF document
    pdf = SimpleDocTemplate(filename, pagesize=letter)
    
    # Define the headers
    headers = ["Visited Date", "Diagnosis/Prognosis", "Record Reference"]

    # Add headers and data to the table
    table_data = [headers] + data

    # Create the table with the data
    table = Table(table_data)

    # Define the style for the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    table.setStyle(style)

    # Build the PDF with the table
    pdf.build([table])

def main():
    input_dir="./data"
    file_names=get_pdf_filenames(input_dir)
    doc_text=extract_text_from_pdf(input_dir+"/" +file_names[0])
    #Visited Date: [YYYY-MM-DD],# Diagnosis/Prognosis: [diagnosis/prognosis],# Record Reference: [record reference] 
    
    query_prefix="""You must give me anything in response except you must retrieve only and only the Visited Date, Diagnosis/Prognosis, and Record Reference for patient from infromation given below. Format the output as follows:

    [Visited Date in format(YYYY-MM-DD)]--[Diagnosis/Prognosis]--[Record Reference] 
    
    
    INFORMATION:
    Record Refernce:"""
    
 
    model = Ollama(model="gemma2:2b")
    result=[]
    for file in file_names:
        doc_text=extract_text_from_pdf(input_dir+"/" +file)
        query_text=query_prefix+file+ """
        """  +doc_text
        result.append(query_rag(query_text,model).strip(" ").replace("\n","").split("--") )    
        
    for res in result:
        print(res)
    create_pdf(result)



def query_rag(query_text: str,model):
    response_text = model.invoke(query_text)
    # generate_pdf_table(response_text)
    return response_text


if __name__ == "__main__":
    main()



