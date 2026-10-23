import os
from pinecone import Pinecone, ServerlessSpec
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, Document, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def index_mixed_data(accounts_data: list, unstructured_docs: list, client_namespace: str):
    """
    Saves both extracted data and plain text data into the same Pinecone namespace
    using a HuggingFace embedding model locally.
    """
    
    # 1. Configure the HuggingFace embedding model globally
    # This automatically downloads and runs the model locally on your machine
    embedding_model_name = "BAAI/bge-small-en-v1.5"
    Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)
    
    # Define correct dimensions for the chosen model (bge-small-en-v1.5 uses 384)
    HF_DIMENSION = 384 

    # 2. Initialize Pinecone
    pc = Pinecone()
    index_name = "fyp-index"  # Matched with production index standard

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=HF_DIMENSION,  # Updated from 1536 to 384
            metric="dotproduct", 
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    pinecone_index = pc.Index(index_name)

    # 3. Configure Vector Store
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index, 
        namespace=client_namespace, 
        add_sparse_vector=True 
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    all_documents = []

    # 4. Process Structured Bank Data
    for acc in accounts_data:
        text_content = f"Account Holder: {acc['full_name']}. Type: {acc['account_type']}. Balance: {acc['balance_usd']} USD."
        metadata = {
            "user_id": acc["user_id"],
            "seller_name": acc["full_name"],  
            "total_amount": acc["balance_usd"],  
            "account_type": acc["account_type"],
            "doc_type": "structured_bank"
        }
        doc = Document(text=text_content, metadata=metadata, doc_id=acc["user_id"])
        all_documents.append(doc)

    # 5. Process Unstructured Plain Text Documents
    for raw_doc in unstructured_docs:
        raw_doc.metadata["doc_type"] = "unstructured_text"
        all_documents.append(raw_doc)

    if not all_documents:
        print("No data found to index.")
        return None

    # 6. Upload everything together (LlamaIndex uses your local HuggingFace model here)
    index = VectorStoreIndex.from_documents(all_documents, storage_context=storage_context)
    print(f"Successfully indexed everything using HuggingFace in namespace: '{client_namespace}'")
    return index