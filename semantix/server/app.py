import os
import time
from flask import Flask, request, jsonify
from langchain_classic.chains.retrieval import create_retrieval_chain

from langchain_community.document_loaders import PyPDFLoader , PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_classic.chains.combine_documents import create_stuff_documents_chain


from flask_cors import CORS  # Import CORS
from waitress import serve

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
def process_pdf(file_path,timeout=1000):
    start_time = time.time()
    # Load the PDF
    loader = PyMuPDFLoader(file_path)
    docs = loader.load()
    first_page_doc = [ docs[0] ]
    print(f"Number of pages loaded: {len(first_page_doc)}")
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(first_page_doc)

    # Initialize embeddings
    embeddings = OllamaEmbeddings(model="llama3")

    # Populate vector store
    vector_store = InMemoryVectorStore.from_documents(
        documents=all_splits,
        embedding=embeddings
    )
    retriever = vector_store.as_retriever()
    chatLLM = ChatOllama(model="llama3")
    prompt = ChatPromptTemplate.from_template("""
    Assume you are a http server and send a json for question asked from provided context.
    Context: {context}
    Question: {input}
    """)
    document_chain =  create_stuff_documents_chain(llm=chatLLM,prompt=prompt)
    retrieval_chain = create_retrieval_chain(retriever,document_chain)
    response = retrieval_chain.invoke({"input": "the retrieved document having loan details like loan amount , loan term and transaction information like borrower , seller , lender and closing information like Date Issued and Closing date  identify loan amount , loan term , borrower , seller , lender and Closing date send response as json string"})    
    comp = ''
    if response["answer"] is not None:
        answer = str(response["answer"])
        start_index = answer.index("```")+3
        end_index = answer.rindex("```")
        comp = answer[start_index:end_index]
        comp = comp.replace('json','')
        comp = comp.replace('/\n',' ')
        print(comp)
    else:
        print(response)
    return comp


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