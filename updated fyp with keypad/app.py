import os
import streamlit as st
from dotenv import load_dotenv
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. Load environment variables
load_dotenv()

# 2. Configure Streamlit Page
st.set_page_config(page_title="RAG Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 Smart Parking System")
st.caption("👨‍💻 Built by **Hamza Aijaz & Mahmood Badar**")

# 3. Configure Global LlamaIndex Settings
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = GoogleGenAI(model="models/gemini-2.5-flash")

# 4. Cache the Engine Initialization
# This prevents reconnecting to Pinecone on every single user message!
@st.cache_resource(show_spinner="Connecting to database...")
def get_query_engine(namespace: str):
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        st.error("Error: Missing PINECONE_API_KEY or GEMINI_API_KEY.")
        st.stop()

    pc = Pinecone()
    index_name = "fyp-index" 
    pinecone_index = pc.Index(index_name)

    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index, 
        namespace=namespace,
        add_sparse_vector=True 
    )

    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    return index.as_query_engine(similarity_top_k=3)

# 5. Sidebar Setup for Namespace Selection
with st.sidebar:
    st.header("⚙️ Configuration")
    client_namespace = st.text_input("Target Namespace:", value="PMS-data")
    st.markdown("---")
    st.markdown("**Model:** Gemini 2.5 Flash\n\n**Embeddings:** BAAI/bge-small-en-v1.5")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []

# 6. Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 7. Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. Chat Input & Processing Loop
if prompt := st.chat_input("Ask a question about your data..."):
    
    # Display user input in UI and add to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Fetch cached engine based on the current namespace
                query_engine = get_query_engine(client_namespace)
                
                # Query the RAG pipeline
                response = query_engine.query(prompt)
                
                # Display response
                st.markdown(response.response)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": response.response})
                
            except Exception as e:
                st.error(f"Execution Error: {e}")