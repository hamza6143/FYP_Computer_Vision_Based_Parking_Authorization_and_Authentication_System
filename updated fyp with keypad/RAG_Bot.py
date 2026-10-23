import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from llama_cloud import AsyncLlamaCloud
from llama_index.core import Document

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Notice we removed the extractor import entirely
from parsing import process_single_file
from indexing import index_mixed_data

load_dotenv()

# We can rename the folder to represent raw document PDFs or text files
DOCUMENTS_FOLDER = Path("./data/documents")

async def main():
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("OPENAI_API_KEY") or not os.getenv("LLAMA_CLOUD_API_KEY"):
        raise ValueError("Error: Missing API keys in your .env file.")

    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    CURRENT_CLIENT_ID = "PMS-data" 
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    client = AsyncLlamaCloud(api_key=api_key)
    
    parsed_docs = []
    
    if DOCUMENTS_FOLDER.exists():
        # 1. Grab all matching documents (.pdf, .docx, .txt)
        files = [f for f in DOCUMENTS_FOLDER.glob("*") if f.suffix.lower() in [".pdf", ".docx", ".txt"]]
        
        print(f"Sending {len(files)} files to LlamaCloud for layout parsing...")
        # 2. Run your LlamaCloud parsing function in parallel
        tasks = [process_single_file(file, client) for file in files]
        parsed_texts = await asyncio.gather(*tasks)
        
        # 3. Package the clean markdown strings straight into LlamaIndex Documents
        for text, file in zip(parsed_texts, files):
            if text:
                doc = Document(text=text, metadata={"filename": file.name})
                parsed_docs.append(doc)

    # 4. Upload straight into Pinecone
    # We pass an empty list [] for accounts_data because we are skipping extraction
    print("Uploading parsed documents directly to Pinecone...")
    index_mixed_data(accounts_data=[], unstructured_docs=parsed_docs, client_namespace=CURRENT_CLIENT_ID)
    
    print("Parsing-only pipeline finished successfully!")

if __name__ == "__main__":
    asyncio.run(main())