import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
if not GROQ_API_KEY:
    st.error("❌ No GROQ API key found. Please set it in the .env file.")
else:
    st.sidebar.success("✅ API key loaded successfully")

llm = ChatGroq(api_key=GROQ_API_KEY, model="llama3-8b-8192")

# Streamlit UI setup
st.set_page_config(page_title="Student AI Assistant", layout="wide")

st.title("🎓 Student AI Assistant")
st.write("Your study companion with multiple helpful modes.")

# Sidebar navigation
mode = st.sidebar.radio(
    "Choose a mode:",
    ["Chat", "Summary", "Flashcards", "File Upload", "Exam Generator"]
)

# --- Mode 1: Chat ---
if mode == "Chat":
    st.header("💬 Chat Mode")
    user_input = st.text_area("Ask me anything:", key="chat_input")
    if st.button("Send", key="chat_button"):
        if user_input.strip():
            try:
                response = llm.invoke(user_input)
                st.success("### Answer")
                st.write(response.content)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
        else:
            st.warning("Please enter a question.")

# --- Mode 2: Summary ---
elif mode == "Summary":
    st.header("📝 Summary Mode")
    text_to_summarize = st.text_area("Paste text to summarize:", key="summary_input")
    if st.button("Summarize", key="summary_button"):
        if text_to_summarize.strip():
            try:
                response = llm.invoke(f"Summarize this text clearly:\n\n{text_to_summarize}")
                st.success("### Summary")
                st.write(response.content)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
        else:
            st.warning("Please paste some text.")

# --- Mode 3: Flashcards ---
elif mode == "Flashcards":
    st.header("🃏 Flashcards Mode")
    topic = st.text_input("Enter a topic for flashcards:", key="flashcard_input")
    if st.button("Generate Flashcards", key="flashcard_button"):
        if topic.strip():
            try:
                response = llm.invoke(f"Create 5 simple Q&A flashcards about: {topic}")
                st.success("### Flashcards")
                flashcards = response.content.split("\n")
                for i, card in enumerate(flashcards, start=1):
                    if card.strip():
                        with st.expander(f"Flashcard {i}"):
                            st.write(card)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
        else:
            st.warning("Please enter a topic.")

# --- Mode 4: File Upload ---
elif mode == "File Upload":
    st.header("📂 File Upload Mode")
    uploaded_file = st.file_uploader("Upload a .txt or .docx file", type=["txt", "docx"])
    if uploaded_file and st.button("Analyze File", key="file_button"):
        try:
            import docx
            if uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")
            else:
                doc = docx.Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs])
            response = llm.invoke(f"Summarize and explain this document:\n\n{text}")
            st.success("### File Analysis")
            st.write(response.content)
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

# --- Mode 5: Exam Generator ---
elif mode == "Exam Generator":
    st.header("📖 Exam Generator Mode")
    subject = st.text_input("Enter a subject or topic:", key="exam_input")
    if st.button("Generate Exam", key="exam_button"):
        if subject.strip():
            try:
                response = llm.invoke(
                    f"Generate 5 multiple-choice questions with 4 options each and highlight the correct answer. Topic: {subject}"
                )
                st.success("### Generated Exam")
                st.write(response.content)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
        else:
            st.warning("Please enter a subject.")
