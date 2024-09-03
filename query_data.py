
# from langchain.vectorstores.chroma import Chroma
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
import sys
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


import sys
import os
import shutil
from langchain.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain.vectorstores.chroma import Chroma


CHROMA_PATH = "chroma"
DATA_PATH = "data"


def populate_database():

    # Check if the database should be cleared (using the --clear flag).

    # Create (or update) the data store.
    documents = load_documents()
    # print(documents[0].metadata["source"].split("/")[-1], documents[1].metadata["page"])
    # print(documents[0])
    
    
    
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    document_loader = PyPDFDirectoryLoader(sys.argv[1])
    return document_loader.load()


def append_references(documents):
    for i in range(len(documents)):        
        source_filename = documents[i].metadata['source'].split("/")[-1]
        page_number = documents[i].metadata['page']
        reference = f"Record Reference: {source_filename} - P{page_number}"
        documents[i].page_content = documents[i].page_content + "\n" + reference
        
def split_documents(documents: list[Document]):
    append_references(documents)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=10,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks: list[Document]):
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        db.persist()
    else:
        pass

def calculate_chunk_ids(chunks):


    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


def generate_pdf_table(response_text, output_pdf=sys.argv[2] +"/output.pdf"):
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
            try:
                
                if "Date of Visit" in cell:
                    visited_date = cell.split(": ", 1)[1]
                elif "Diagnosis/Prognosis" in cell:
                    diagnosis_prognosis = cell.split(": ", 1)[1]
                elif "Record Reference" in cell:
                    record_reference = cell.split(": ", 1)[1]
            except:
                continue
        # Add row data to the table
        pdf.cell(63, 10, visited_date, border=1)
        pdf.cell(63, 10, diagnosis_prognosis, border=1)
        pdf.cell(63, 10, record_reference, border=1)
        pdf.ln(10)

    # Output the PDF
    pdf.output(output_pdf)


def main():
    populate_database()
    query_text = """You must not return anything You must only and only Retrieve the Visited Date, Diagnosis/Prognosis, and Record Reference for all patients from database and display them in a chronological manner. Format the output as follows:

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
    print(response_text)
    generate_pdf_table(response_text)
    return response_text


if __name__ == "__main__":
    main()




