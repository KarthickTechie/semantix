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

# Define queries based on observed content
    queries = [
        "Employee Name",
        "Employee ID",
        "Date of Joining",
        "Pay Period",
        "Pay Date",
        "Total Net Pay",
        "Basic",
        "House Rent Allowance",
        "Income Tax",
        "Provident Fund",
        "Gross Earnings",
        "Total Deductions",
        "employee name",
        "employee number",
        "date of joining",
        "total earnings",
        "total deductions",
        "net amount"
    ]
    results = {query.lower().replace(" ", "_"): None for query in queries}

    # Perform similarity search and parse results
    for query in queries:
        search_results = vector_store.similarity_search(query, k=1)
        if search_results and time.time() - start_time < timeout:
            content = search_results[0].page_content
            lines = content.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                if query in line:
                    # Look for value in the same line or next line
                    if ":" in line:
                        value = line.split(":")[1].strip()
                        results[query.lower().replace(" ", "_")] = value if value else "Not found"
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if "Rs." in next_line or "₹" in next_line:
                            results[query.lower().replace(" ", "_")] = next_line
                        else:
                            results[query.lower().replace(" ", "_")] = next_line if next_line else "Not found"
        elif time.time() - start_time >= timeout:
            raise TimeoutError("Processing exceeded 1000-second timeout limit")

    expected_fields = {
        "employee_name": "Not found",
        "employee_id": "Not found",
        "date_of_joining": "Not found",
        "pay_period": "Not found",
        "pay_date": "Not found",
        "total_net_pay": "Not found",
        "basic": "Not found",
        "house_rent_allowance": "Not found",
        "income_tax": "Not found",
        "provident_fund": "Not found",
        "gross_earnings": "Not found",
        "total_deductions": "Not found",
        "employee_number":"Not found",
        "total_earnings":"Not found",
        "total_deductions":"Not found",
        "net_amount":"Not found",

    }
    results.update({k: v for k, v in results.items() if v is not None})
    results = {k: expected_fields[k] if v is None else v for k, v in results.items()}

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
            result = process_pdf(file_path,timeout=1000) 
            return jsonify(result), 200
        except TimeoutError:
            return jsonify({"error": "Request timed out after 1000 seconds. Please check Ollama server or file size."}), 408
        except Exception as e:
            return jsonify({"error": str(e)}), 500        
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)  
    else:
        return jsonify({"error": "Invalid file format. Please upload a PDF"}), 400

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)