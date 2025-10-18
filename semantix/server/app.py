import os
import time
from flask import Flask, request, jsonify
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from flask_cors import CORS  # Import CORS
from waitress import serve

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
def process_pdf(file_path,timeout=1000):
    start_time = time.time()
    # Load the PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    print(f"Number of pages loaded: {len(docs)}")

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)

    # Initialize embeddings
    embeddings = OllamaEmbeddings(model="llama3")

    # Populate vector store
    vector_store = InMemoryVectorStore.from_documents(
        documents=all_splits,
        embedding=embeddings
    )

    # Perform similarity search for key details
    queries = [
        "What is the employee name?",
        "What is the employee number?",
        "What is the total earnings?",
        "What is the total deductions?",
        "What is the net amount?"
    ]
    results = {query.split("What is the ")[1].replace("?", "").lower(): None for query in queries}

    for query in queries:
        search_results = vector_store.similarity_search(query, k=1)
        if search_results and time.time() - start_time < timeout:
            content = search_results[0].page_content
            parts = content.split("\n")
            for i, line in enumerate(parts):
                if "Employee Name" in line:
                    results["employee name"] = parts[i + 1].strip() if i + 1 < len(parts) else "Not found"
                elif "Employee Number" in line:
                    results["employee number"] = parts[i + 1].strip() if i + 1 < len(parts) else "Not found"
                elif "Date of Joining" in line:
                    results["date of joining"] = parts[i + 1].strip() if i + 1 < len(parts) else "Not found"
                elif "Total Earnings" in line:
                    results["gross earnings"] = parts[i + 1].strip() if i + 1 < len(parts) else "Not found"
                elif "Total Deductions" in line:
                    results["total deductions"] = parts[i + 1].strip() if i + 1 < len(parts) else "Not found"
                elif "Net Amount" in line:
                    results["net amount"] = parts[i + 1].strip() if i + 1 < len(parts) else "Not found"
        elif time.time() - start_time >= timeout:
            raise TimeoutError("Processing exceeded 1000-second timeout limit")

    return results
@app.route('/getSalaryDetails', methods=['POST'])
def get_salary_details():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join("./uploads", file.filename)
        print(f"file_path: {len(file_path)}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        try:
            result = process_pdf(file_path,timeout=1000)  # 1000-second timeout
            return jsonify(result), 200
        except TimeoutError:
            return jsonify({"error": "Request timed out after 1000 seconds. Please check Ollama server or file size."}), 408
        except Exception as e:
            return jsonify({"error": str(e)}), 500        
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up the uploaded file
    else:
        return jsonify({"error": "Invalid file format. Please upload a PDF"}), 400

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)