import os
from dotenv import load_dotenv
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

load_dotenv()

# 2. Configure Gemini 2.5 Flash as the global LLM framework and huggingface
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = GoogleGenAI(model="models/gemini-2.5-flash")

def initialize_chat_engine(question: str, client_namespace: str):
    """
    Connects to Pinecone using a dynamic namespace and answers a question
    using the Gemini 2.5 Flash model.
    """
    # 1. Check API Keys
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        raise ValueError("Error: Missing PINECONE_API_KEY or GEMINI_API_KEY in your .env file.")


    # 3. Initialize Pinecone client
    pc = Pinecone()
    index_name = "fyp-index"  # Matches index created in your pipeline
    pinecone_index = pc.Index(index_name)

    # 4. Connect to the specific client namespace dynamically
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index, 
        namespace=client_namespace,
        add_sparse_vector=True  # Must match your native hybrid indexing configuration
    )

    # 5. Load the index structure from the active vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # 6. Create the query engine
    query_engine = index.as_query_engine(similarity_top_k=3)

    # 7. Run the query and return response
    response = query_engine.query(question)
    return response

if __name__ == "__main__":
    TEST_CLIENT = "PMS-data"  # Your target namespace folder
    
    print(f"==================================================")
    print(f" Chatbot Active for Namespace: '{TEST_CLIENT}'")
    print(f" Model: Gemini 2.5 Flash + HuggingFace Embeddings")
    print(f" (Type 'exit' or 'quit' to stop the chat)")
    print(f"==================================================")
    
    # This loop keeps running forever until you type 'exit'
    while True:
        print("\n") # Adds a clean empty space between turns
        user_question = input("You: ").strip()
        
        # Check if the user wants to close the program
        if user_question.lower() in ["exit", "quit"]:
            print("Closing chat. Goodbye!")
            break
            
        # Skip if the user accidentally pressed enter without typing anything
        if not user_question:
            continue
            
        print(f"Bot: Thinking...")
        try:
            # Send the question to your main function
            answer = initialize_chat_engine(user_question, client_namespace=TEST_CLIENT)
            print("\n--- Gemini Response ---")
            print(answer)
            print("-" * 23)
            
        except Exception as e:
            print(f"\nExecution Error: {e}")
            