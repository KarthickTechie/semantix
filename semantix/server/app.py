from flask import Flask, request, jsonify
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_community.retrievers import BM25Retriever
from langchain_classic.chains.retrieval_qa.base import RetrievalQA  # Corrected import
from langchain_classic.prompts import PromptTemplate
from langchain_classic.chains.llm import LLMChain
from langchain_classic.schema import BaseRetriever, Document
import os
import time
from flask_cors import CORS
from waitress import serve

app = Flask(__name__)
CORS(app)

# Custom Hybrid Retriever Class
class HybridRetriever(BaseRetriever):
    def __init__(self, semantic_retriever, bm25_retriever):
        self.semantic_retriever = semantic_retriever
        self.bm25_retriever = bm25_retriever

    def _get_relevant_documents(self, query):  # Corrected to _get_relevant_documents
        semantic_results = self.semantic_retriever.invoke(query)
        bm25_results = self.bm25_retriever.invoke(query)
        combined = semantic_results[:2] + [doc for doc in bm25_results if doc not in semantic_results][:1]
        return combined[:3]
    
def process_pdf(file_path, timeout=1000):
    start_time = time.time()

    # Load and split
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    if not docs:
        raise ValueError("No content extracted from PDF")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n", "  ", "₹", "Rs."]
    )
    all_splits = text_splitter.split_documents(docs)

    # Embeddings and LLM with Llama3
    embeddings = OllamaEmbeddings(model="llama3")
    llm = OllamaLLM(model="llama3", temperature=0.1)

    # Vector store for semantic search
    vector_store = InMemoryVectorStore.from_documents(all_splits, embeddings)
    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # BM25 for keyword search
    bm25_retriever = BM25Retriever.from_documents(all_splits)
    bm25_retriever.k = 3

    # Initialize custom hybrid retriever
    hybrid_retriever = HybridRetriever(semantic_retriever, bm25_retriever)

    # Custom prompt for structured extraction
    prompt_template = """
    Extract the following salary components as JSON from the context. Use exact values with currency (e.g., ₹14,000.00 or Rs.80,000.00). If not found, use "Not found".
    Components: Employee Name, Employee ID, Basic Pay, HRA, Total Earnings, Income Tax, Provident Fund, Total Deductions, Net Amount.
    Context: {context}
    Query: {question}
    Output only valid JSON.
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # RAG chain with hybrid retriever
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=hybrid_retriever,  # Now a proper retriever instance
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        # Run query with RetrievalQA
        question = "Extract all salary components from this payslip."
        result = qa_chain.invoke({"query": question})
        extracted_json = result["result"]
    except (AttributeError, ImportError):
        # Fallback to LLMChain with manual context
        question = "Extract all salary components from this payslip."
        context = "\n".join([doc.page_content for doc in hybrid_retriever._get_relevant_documents(question)])
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        extracted_json = llm_chain.run({"context": context, "question": question})

    if time.time() - start_time >= timeout:
        raise TimeoutError("Processing exceeded 1000-second timeout limit")

    return {"extracted_data": extracted_json, "sources": [doc.page_content[:100] + "..." for doc in result["source_documents"]] if "result" in locals() else []}

@app.route('/getSalaryDetails', methods=['POST'])
def get_salary_details():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join("./uploads", file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        try:
            result = process_pdf(file_path, timeout=1000)
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