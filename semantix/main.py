import asyncio
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore

# Load the PDF
filepath = "./data/OCT-22.pdf"
loader = PyPDFLoader(filepath)
docs = loader.load()
print(f"Number of pages loaded: {len(docs)}")

# Print first 200 characters of the first page and its metadata
print(f"\nFirst 200 characters of page 0:\n{docs[0].page_content[:200]}\n")
print(f"Metadata of page 0: {docs[0].metadata}\n")

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)
print(f"Number of document chunks: {len(all_splits)}\n")

# Initialize embeddings
embeddings = OllamaEmbeddings(model="llama3")

# Generate embeddings for the first two splits and verify their length
if len(all_splits) >= 2:
    vector_1 = embeddings.embed_query(all_splits[0].page_content)
    vector_2 = embeddings.embed_query(all_splits[1].page_content)
    assert len(vector_1) == len(vector_2), "Vectors have different lengths"
    print(f"Generated vectors of length {len(vector_1)}\n")
    print(f"First 10 elements of vector_1: {vector_1[:10]}\n")
else:
    print("Not enough chunks to compare vectors.\n")

# Initialize and populate the vector store
vector_store = InMemoryVectorStore.from_documents(
    documents=all_splits,
    embedding=embeddings
)

# Perform similarity search (synchronous)
results = vector_store.similarity_search("What is the employee name?", k=1)

# Print the top result
if results:
    print(f"Top result for 'What is the employee name?':\n{results[0].page_content}\n")
    print(f"Metadata: {results[0].metadata}")
else:
    print("No results found.")

# If you need to use the async version, define an async function
# async def async_search():
#     results = await vector_store.asimilarity_search("What is the employee name?", k=1)
#     if results:
#         print(f"Async top result for 'What is the employee name?':\n{results[0].page_content}\n")
#         print(f"Metadata: {results[0].metadata}")
#     else:
#         print("No results found in async search.")

# # Run the async search
# if __name__ == "__main__":
#     asyncio.run(async_search())