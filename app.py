import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import os

# ✅ Must be the first Streamlit command
st.set_page_config(page_title="Student AI Assistant", layout="wide", initial_sidebar_state="expanded")

# ✅ Custom Light Theme with Colorful Headings
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #f7faff !important;
        color: #222 !important;
    }

    h1 {
        color: #1a4f8b !important; /* Deep royal blue */
    }

    h2 {
        color: #2c7a7b !important; /* Teal green */
    }

    .stTextInput>div>div>input, .stTextArea textarea {
        background-color: #ffffff !important;
        border: 1px solid #ddd;
        color: #333;
        padding: 0.5rem;
        border-radius: 8px;
    }

    .stButton button {
        background-color: #4da6ff;
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        border: none;
    }

    .stButton button:hover {
        background-color: #3399ff;
    }

    .stExpander, .stTextArea, .stTextInput {
        border-radius: 10px !important;
        border: 1px solid #d9e4f5 !important;
        box-shadow: 0 0 5px rgba(0,0,0,0.05);
    }

    ::placeholder {
        color: #888 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ Load API key (local .env OR Streamlit Secrets)
load_dotenv()
API_KEY = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("API key not found. Please set GROQ_API_KEY in .env (local) or Streamlit Secrets (cloud).")

# ✅ Initialize Groq + LLaMA3
llm = ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=API_KEY)

# ✅ Helper to call LLM
def generate_response(system_msg, user_input):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", "{input}")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"input": user_input})

# ✅ App Title
st.title("🎓 Student AI Assistant (Groq + LLaMA3)")
st.write("Ask anything related to your studies — summaries, quizzes, MCQs, and more!")

# ✅ Sidebar: Mode selector
mode = st.sidebar.selectbox("Choose a mode", ["Chat", "Summary", "Flashcards", "File Upload", "Exam Generator"])

# --- Chat Mode ---
if mode == "Chat":
    st.subheader("💬 Ask me anything")
    question = st.text_input("Enter your question:")
    if st.button("Submit", key="chat"):
        if question:
            response = generate_response("You're a helpful tutor.", question)
            st.success(response)

# --- Summary Mode ---
elif mode == "Summary":
    st.subheader("📝 Text Summarizer")
    text = st.text_area("Paste your content here:")
    if st.button("Summarize"):
        if text:
            response = generate_response("Summarize the text into clear bullet points.", text)
            st.success(response)

# --- Flashcards Mode ---
elif mode == "Flashcards":
    st.subheader("🧠 Generate Flashcards")
    topic = st.text_area("Enter a topic or content:")
    if st.button("Generate Flashcards"):
        if topic:
            response = generate_response(
                "Create 5 Quizizz-style flashcards in this format:\nQ: [question]\nA: [answer]\nOnly include educational content.",
                topic
            )
            cards = []
            for block in response.strip().split("\n"):
                if block.startswith("Q:"):
                    q = block[2:].strip()
                elif block.startswith("A:"):
                    a = block[2:].strip()
                    cards.append((q, a))

            if cards:
                for i, (q, a) in enumerate(cards, 1):
                    with st.expander(f"Flashcard {i}: {q}"):
                        st.markdown(f"**Answer:** {a}")
            else:
                st.warning("Could not generate flashcards. Try rephrasing your input.")

# --- File Upload Mode ---
elif mode == "File Upload":
    st.subheader("📄 Upload PDF or DOCX")
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx"])
    if uploaded_file and st.button("Process File"):
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.read())
        loader = PyPDFLoader(uploaded_file.name) if uploaded_file.name.endswith(".pdf") else Docx2txtLoader(uploaded_file.name)
        documents = loader.load()
        content = "\n".join(doc.page_content for doc in documents)
        st.text_area("📚 File Content", content[:3000])
        response = generate_response("Summarize this document for easier revision.", content)
        st.success(response)

# --- Exam Generator Mode ---
elif mode == "Exam Generator":
    st.subheader("🧪 Generate MCQs")
    input_text = st.text_area("Enter topic or material for MCQs:")
    if st.button("Generate MCQs"):
        if input_text:
            response = generate_response(
                "Make 5 neat multiple-choice questions (A–D) with the correct answer marked clearly. Use clean formatting.",
                input_text
            )
            st.markdown(response.replace("**", "*"))  # Clean display
