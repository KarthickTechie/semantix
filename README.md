# PDF Salary Component Extractor

## Overview

This project is a simple Flask-based web application that uses LangChain to process PDF files and extract salary component information. It reads a PDF, splits it into manageable chunks, generates embeddings using Ollama, and stores them in an in-memory vector store for efficient retrieval.

## Features

- Upload PDF files containing salary-related information.
- Extract and return salary components using LangChain's text processing and embedding capabilities.
- Lightweight in-memory vector store for quick document retrieval.
- CORS-enabled Flask API for cross-origin requests.
- Served using Waitress for production-ready deployment.

## Prerequisites

Before running the project, ensure you have the following installed:

- Python 3.8+
- Git
- Ollama (for embeddings, see [Ollama documentation](https://ollama.ai/))
- A PDF file containing salary component details for testing

## Installation

1. **Clone the repository**:

   ```bash
   git clone <your-repository-url>
   cd <your-repository-name>
   ```

2. **Set up a virtual environment** (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install flask langchain-community langchain-ollama pypdf flask-cors waitress
   ```

4. **Set up Ollama**:
   - Install Ollama following the instructions at [Ollama's official site](https://ollama.ai/).
   - Ensure the Ollama server is running locally to generate embeddings.

## Usage

1. **Run the application**:

   ```bash
   python app.py
   ```

   The application will start a Flask server using Waitress, typically on `http://localhost:5000`.

2. **API Endpoint**:

   - **Endpoint**: `POST /extract-salary`
   - **Request**: Send a PDF file in a multipart/form-data request.
     ```bash
     curl -X POST -F "file=@/path/to/your/salary.pdf" http://localhost:5000/extract-salary
     ```
   - **Response**: JSON object containing extracted salary components.

3. **Example Response**:
   ```json
   {
     "salary_components": {
       "basic_salary": "50000",
       "allowances": "10000",
       "bonuses": "5000",
       ...
     }
   }
   ```

## Project Structure

```
├── app.py                  # Main Flask application
├── requirements.txt        # Project dependencies
├── README.md              # Project documentation (this file)
└── venv/                  # Virtual environment (if used)
```

## Dependencies

The project relies on the following Python packages:

- `flask`: Web framework for building the API.
- `langchain-community`: Core LangChain utilities for document processing.
- `langchain-ollama`: Ollama embeddings for text vectorization.
- `pypdf`: PDF file parsing.
- `flask-cors`: Enables cross-origin requests.
- `waitress`: Production-ready WSGI server.

Install them using:

```bash
pip install -r requirements.txt
```

## Notes

- Ensure the PDF file contains structured salary information for accurate extraction.
- The application uses an in-memory vector store (`InMemoryVectorStore`), so data is not persisted between sessions.
- For production, consider replacing `InMemoryVectorStore` with a persistent vector store like FAISS or Chroma.
- Adjust the `RecursiveCharacterTextSplitter` parameters in the code if you need different chunk sizes or overlap for better text processing.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or suggestions, feel free to open an issue or contact the repository owner.
