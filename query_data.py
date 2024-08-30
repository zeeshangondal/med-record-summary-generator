import argparse
# from langchain.vectorstores.chroma import Chroma
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from get_embedding_function import get_embedding_function

import warnings
warnings.filterwarnings("ignore")

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""



from fpdf import FPDF

from fpdf import FPDF

def generate_pdf_table(response_text, output_pdf="output.pdf"):
    # Define headers
    headers = ["Visited Date", "Diagnosis/Prognosis", "Record Reference"]
    
    # Split the response text into rows based on newlines
    rows = response_text.strip().split("\n")
    
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
        visited_date = diagnosis_prognosis = record_reference = "Not provided"
        
        # Split row into cells based on commas
        cells = row.split(", ")
        
        for cell in cells:
            if "Date of Visit" in cell:
                visited_date = cell.split(": ", 1)[1]
            elif "Diagnosis/Prognosis" in cell:
                diagnosis_prognosis = cell.split(": ", 1)[1]
            elif "Record Reference" in cell:
                record_reference = cell.split(": ", 1)[1]
        
        # Add row data to the table
        pdf.cell(63, 10, visited_date, border=1)
        pdf.cell(63, 10, diagnosis_prognosis, border=1)
        pdf.cell(63, 10, record_reference, border=1)
        pdf.ln(10)

    # Output the PDF
    pdf.output(output_pdf)


def main():
    
    query_text = """Retrieve the Visited Date, Diagnosis/Prognosis, and Record Reference for all patients from database and display them in a chronological manner. Format the output as follows:

    Visited Date: [Date], Diagnosis/Prognosis, Record Reference: [File Name] - [Page Number].
    Ensure that each entry follows this exact format and is presented in a list."""
    query_rag(query_text)


def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    # print(prompt)

    model = Ollama(model="mistral")
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    generate_pdf_table(response_text)
    print(response_text)
    return response_text


if __name__ == "__main__":
    main()




