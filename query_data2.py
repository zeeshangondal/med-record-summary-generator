import argparse
from langchain_community.llms.ollama import Ollama
import os
from PyPDF2 import PdfReader
import sys

from fpdf import FPDF
from datetime import datetime

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





from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime
import re

def sanitize_date(date_str):
    """Convert various date formats to a uniform YYYY,MM,DD format."""
    # Define possible date formats
    date_formats = [
        "%Y-%m-%d",  # Format like 2000-03-08
        "%d/%m/%Y",  # Format like 20/08/2020
        "%d-%m-%Y"   # Format like 08-03-2000
    ]

    # Remove unwanted characters and standardize the date separators
    cleaned_date = re.sub(r'[^\d/-]', '', date_str)

    for fmt in date_formats:
        try:
            # Try parsing the date with the current format
            parsed_date = datetime.strptime(cleaned_date, fmt)
            # Return the date in the desired format YYYY,MM,DD
            return parsed_date.strftime("%Y,%m,%d")
        except ValueError:
            continue

    # If no formats matched, return the original cleaned date or an empty string
    return cleaned_date

def sort_by_date(data):
    """Sort data rows based on the sanitized date in descending order."""
    # Convert the sanitized date string back to a datetime object for sorting
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y,%m,%d")
        except ValueError:
            return datetime.min  # Return a minimal date for unsorted or invalid dates

    # Add the sanitized date to each row, sort, and remove the date again
    sorted_data = sorted(data, key=lambda row: parse_date(sanitize_date(row[0])), reverse=True)
    return sorted_data

def create_pdf(data, filename=sys.argv[2]+"/output.pdf"):
    # Create a PDF document with adjusted margins
    pdf = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=inch*0.75,
        leftMargin=inch*0.75,
        topMargin=inch*0.75,
        bottomMargin=inch*0.75
    )

    # Define the headers
    headers = ["Visited Date", "Diagnosis/Prognosis", "Record Reference"]

    # Process and sort the data
    sanitized_data = []
    for row in data:
        # Sanitize the date (first column) in each row
        sanitized_row = [sanitize_date(row[0])] + row[1:]
        sanitized_data.append(sanitized_row)

    # Sort the data by the sanitized date
    sorted_data = sort_by_date(sanitized_data)

    # Add headers and sorted data to the table
    table_data = [headers] + sorted_data

    # Define column widths (adjust as necessary)
    column_widths = [2*inch, 3*inch, 2.5*inch]  # Example widths, adjust to fit your content

    # Create the table with the data
    table = Table(table_data, colWidths=column_widths)

    # Define the style for the table
    style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Text size is set to 8 points
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold for headers
        ('FONTSIZE', (0, 0), (-1, 0), 10),  # Text size is set to 10 points for headers
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to the top of cells
    ])

    table.setStyle(style)

    # Build the PDF with the table
    pdf.build([table])



def main():
    input_dir= sys.argv[1]
    file_names=get_pdf_filenames(input_dir)
    
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
        
        result.append(query_rag(query_text,model).strip(" ").replace("\n","").replace("*","").split("--") )    
        
    for res in result:
        print(res)
    create_pdf(result)



def query_rag(query_text: str,model):
    response_text = model.invoke(query_text)
    # generate_pdf_table(response_text)
    return response_text


if __name__ == "__main__":
    main()



