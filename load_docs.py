import fitz  
import os

def extract_text_from_pdfs(folder_path):
    all_docs = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(folder_path, file_name)
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            all_docs.append({"filename": file_name, "content": text})
    return all_docs
