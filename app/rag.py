import os
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker

# ==========================================
# STEP 1: MODULAR DOCUMENT LOADING
# ==========================================
def load_all_documents(directory_path: str) -> list:
    """Scans a directory and automatically uses the correct loader for each file type."""
    all_documents = []
    
    if not os.path.exists(directory_path):
        print(f"Warning: Directory {directory_path} not found.")
        return all_documents

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if ext == '.txt':
                loader = TextLoader(file_path)
            elif ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif ext == '.docx':
                loader = Docx2txtLoader(file_path)
            elif ext == '.csv':
                loader = CSVLoader(file_path)
            elif ext == '.md':
                loader = UnstructuredMarkdownLoader(file_path)
            elif ext == '.pptx':
                loader = UnstructuredPowerPointLoader(file_path)
            elif ext == '.xlsx':
                loader = UnstructuredExcelLoader(file_path)
            else:
                continue # Skip unsupported files
                
            all_documents.extend(loader.load())
            print(f"Loaded: {filename}")
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
    return all_documents


# ==========================================
# STEP 2: MODULAR CHUNKING STRATEGY (UPGRADED)
# ==========================================
def chunk_documents(documents: list) -> list:
    """Uses Semantic Chunking to group text by meaning rather than character count."""
    if not documents:
        return []
        
    # Semantic chunking requires an embedding model to measure the "distance" in meaning between sentences
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")     
      
    # Initialize the Semantic Chunker
    semantic_splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile", # Splits when a sentence is significantly different from the last one
        breakpoint_threshold_amount=80 # The sensitivity (higher = fewer, larger chunks)
    )
    
    # Because SemanticChunker expects pure strings for its initial split, 
    # we iterate through the loaded Document objects safely
    return semantic_splitter.split_documents(documents)


# ==========================================
# STEP 3: MODULAR EMBEDDING & RETRIEVAL
# ==========================================
def create_hybrid_retriever(chunks: list):
    """Creates the vector store, BM25, and combines them into a Hybrid Retriever."""
    if not chunks:
        return None
        
    # A. Dense Retriever (Semantic Vector Search)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(chunks, embeddings)
    faiss_retriever = vector_store.as_retriever(search_kwargs={"k": 2})

    # B. Sparse Retriever (Exact Keyword Search)
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = 2

    # C. Combine into Hybrid Search
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever], 
        weights=[0.5, 0.5] 
    )
    return hybrid_retriever


# ==========================================
# INITIALIZATION & TOOL EXPORT
# ==========================================
# 1. Define where your course materials live
COURSE_MATERIALS_DIR = r"C:\Users\Yash\OneDrive\Desktop\Ai powered college learning assistant\course_materials"

# 2. Run the pipeline
raw_docs = load_all_documents(COURSE_MATERIALS_DIR)
doc_chunks = chunk_documents(raw_docs)
course_retriever = create_hybrid_retriever(doc_chunks)

# 3. Create the LangChain Tool
@tool
def search_course_material(query: str) -> str:
    """Use this tool to search the syllabus and study guides for course material.
    DO NOT use this tool for general conversation, greetings, or basic math."""
    
    if not course_retriever:
        return "No course materials are currently loaded."
        
    results = course_retriever.invoke(query)
    
    formatted_results = []
    for doc in results:
        # 1. Strip the ugly C:\ folder path, keep only the file name
        raw_source = doc.metadata.get("source", "Course Material")
        clean_source_name = os.path.basename(raw_source)
        
        # 2. Fix the 0-indexed page number by adding + 1
        page_num = doc.metadata.get("page")
        if page_num is not None:
            clean_source_name += f" (Page {page_num + 1})"
            
        # 3. Format it for the extractor
        formatted_text = f"SOURCE: {clean_source_name} | CONTENT: {doc.page_content}"
        formatted_results.append(formatted_text)
        
    return "\n\n".join(formatted_results)