import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import os

load_dotenv()

# Initialize LLM
llm = ChatGroq(temperature=0, model_name="llama3-8b-8192")

# Helper for output formatting
def generate_response(system_msg, user_input):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", "{input}")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"input": user_input})

# UI Setup
st.set_page_config(page_title="Student AI Assistant", layout="wide")
st.title("🎓 Student AI Assistant (Groq + LLaMA3)")
st.write("Ask anything related to your studies — summaries, quizzes, MCQs, and more!")

# Mode Selection
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
