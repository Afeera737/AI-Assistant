# app.py  (FULL FILE)
import streamlit as st
import os
import re
from dotenv import load_dotenv
import docx2txt

# Prefer pypdf (new name). Fall back to PyPDF2 if needed.
PdfReader = None
try:
    from pypdf import PdfReader  # recommended
except Exception:
    try:
        from PyPDF2 import PdfReader  # legacy
    except Exception:
        PdfReader = None

# Try to import langchain + groq support (optional)
LANGCHAIN_AVAILABLE = False
ChatGroq = None
ChatPromptTemplate = None
StrOutputParser = None
llm = None

try:
    from langchain_groq import ChatGroq
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

# Must be the very first Streamlit command
st.set_page_config(page_title="Student AI Assistant", layout="wide", initial_sidebar_state="expanded")

# Simple theme/styles
st.markdown(
    """
    <style>
    body, .stApp { background-color: #f7faff !important; color: #222 !important; }
    h1 { color: #1a4f8b !important; }
    h2 { color: #2c7a7b !important; }
    .stTextInput>div>div>input, .stTextArea textarea {
        background-color: #fff !important; border: 1px solid #ddd; padding: 0.5rem; border-radius: 8px;
    }
    .stButton button { background-color: #4da6ff; color: white; border-radius: 6px; }
    .stButton button:hover { background-color: #3399ff; }
    .stExpander, .stTextArea, .stTextInput { border-radius: 10px !important; border: 1px solid #d9e4f5 !important; }
    ::placeholder { color: #888 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Load environment (.env)
load_dotenv()

# Safe secret loader: try Streamlit secrets, then fallback to environment var
def get_groq_api_key():
    # Try st.secrets (Streamlit cloud / local secrets file) but don't crash if it's missing
    try:
        # Using bracket access so missing file/keys raise and we can fallback gracefully
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        # fallback to environment variable (.env or system env)
        return os.getenv("GROQ_API_KEY")

API_KEY = get_groq_api_key()

# show boolean debug so you know it's loaded (DO NOT print API_KEY itself)
st.sidebar.write("API key loaded?", bool(API_KEY))
if not API_KEY:
    st.sidebar.warning("GROQ_API_KEY not found. Set it in .env or Streamlit Secrets (see instructions).")

# Initialize Groq + model (only if langchain_groq available and an API key present)
if LANGCHAIN_AVAILABLE and API_KEY:
    try:
        # Recommended lightweight production model on Groq for chat-like usage:
        # - 'llama-3.1-8b-instant'  -> fast & cheap (good for demos/interactive apps)
        # Switch to e.g. 'llama-3.3-70b-versatile' for higher quality (cost > latency).
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=API_KEY)
        st.sidebar.success("LLM client initialized.")
    except Exception as e:
        llm = None
        st.sidebar.error(f"LLM init failed: {e}")
else:
    if not LANGCHAIN_AVAILABLE:
        st.sidebar.info("langchain_groq not installed — app will run in DEMO mode.")
    else:
        st.sidebar.info("API key missing — app will run in DEMO mode.")

DEMO_MODE = llm is None
if DEMO_MODE:
    st.warning("DEMO MODE: LLM backend not available. App will use safe, local demo responses. For full AI, install `langchain-groq` and set GROQ_API_KEY in Streamlit Secrets.")

# ---------- Helpers ----------
def demo_response(system_msg: str, user_input: str) -> str:
    """Deterministic demo responder used when LLM isn't available."""
    text = (user_input or "").strip()
    if not text:
        return "No input provided."

    # Summarize: split into sentences and return top bullets
    if "summar" in system_msg.lower():
        sents = re.split(r'(?<=[.!?])\s+', text)
        bullets = [s.strip() for s in sents if s.strip()][:5]
        if bullets:
            return "\n".join([f"- {b}" for b in bullets])
        return "Couldn't extract clear sentences to summarize."

    # Flashcards heuristic
    if "flashcard" in system_msg.lower():
        sents = re.split(r'(?<=[.!?])\s+', text)
        cards = []
        for i in range(5):
            if i < len(sents):
                q = f"What does this mean: \"{sents[i][:60].strip()}\"?"
                a = sents[i].strip()
            else:
                q = f"Define key concept {i+1}."
                a = "Short definition or key point."
            cards.append(f"Q: {q}\nA: {a}")
        return "\n\n".join(cards)

    # MCQ heuristic
    if "multiple-choice" in system_msg.lower() or "mcq" in system_msg.lower() or "multiple choice" in system_msg.lower():
        mcqs = []
        for i in range(1, 6):
            mcqs.append(
                f"{i}. Example question about the topic:\nA) Option 1\nB) Option 2\nC) Option 3\nD) Option 4\n**Answer:** A"
            )
        return "\n\n".join(mcqs)

    # Default chat: echo first two sentences concisely
    sents = re.split(r'(?<=[.!?])\s+', text)
    concise = " ".join(sents[:2]) if sents else text
    return f"Demo reply — concise explanation:\n{concise}"

def generate_response(system_msg: str, user_input: str) -> str:
    """Use real LLM if available, otherwise demo_response. Errors fall back to demo_response but surface a short note."""
    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("user", "{input}")
            ])
            chain = prompt | llm | StrOutputParser()
            return chain.invoke({"input": user_input})
        except Exception as e:
            # fallback to demo but surface a short note for debugging
            return demo_response(system_msg, user_input) + f"\n\n[Note: LLM call failed: {e}]"
    else:
        return demo_response(system_msg, user_input)

def read_uploaded_file_to_text(uploaded_file) -> str:
    """Read PDF or DOCX from uploaded_file to plain text using pypdf / PyPDF2 / docx2txt."""
    if not uploaded_file:
        return ""
    os.makedirs("tmp_uploads", exist_ok=True)
    path = os.path.join("tmp_uploads", uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())

    lower = uploaded_file.name.lower()
    if lower.endswith(".pdf"):
        if PdfReader is None:
            return "[Error reading PDF: pypdf/PyPDF2 not installed]"
        try:
            reader = PdfReader(path)
            text = ""
            # pypdf & PyPDF2 differ slightly; handle generically
            for p in getattr(reader, "pages", reader.pages if hasattr(reader, "pages") else []):
                page_text = p.extract_text() if hasattr(p, "extract_text") else p.extractText()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            return f"[Error reading PDF: {e}]"
    elif lower.endswith(".docx"):
        try:
            return docx2txt.process(path) or ""
        except Exception as e:
            return f"[Error reading DOCX: {e}]"
    else:
        return "[Unsupported file type]"

# ---------- UI ----------
st.title("🎓 Student AI Assistant (Demo-capable)")

mode = st.sidebar.selectbox("Choose a mode", ["Chat", "Summary", "Flashcards", "File Upload", "Exam Generator"])

if mode == "Chat":
    st.subheader("💬 Chat (Ask anything)")
    question = st.text_input("Enter your question:")
    if st.button("Submit", key="chat"):
        if question:
            with st.spinner("Thinking..."):
                response = generate_response("You're a helpful tutor.", question)
            st.success(response)
        else:
            st.warning("Please enter a question.")

elif mode == "Summary":
    st.subheader("📝 Summarizer")
    text = st.text_area("Paste content here:")
    if st.button("Summarize", key="summ"):
        if text:
            with st.spinner("Summarizing..."):
                out = generate_response("Summarize the text into clear bullet points.", text)
            st.text_area("Summary", out, height=250)
        else:
            st.warning("Please paste some text to summarize.")

elif mode == "Flashcards":
    st.subheader("🧠 Flashcards")
    topic = st.text_area("Enter topic or content:")
    if st.button("Generate Flashcards", key="fc"):
        if topic:
            with st.spinner("Generating flashcards..."):
                response = generate_response("Create 5 Quizizz-style flashcards in this format:\nQ: [question]\nA: [answer]\nOnly include educational content.", topic)
            cards = []
            q = a = None
            for block in response.strip().split("\n"):
                if block.startswith("Q:"):
                    q = block[2:].strip()
                elif block.startswith("A:"):
                    a = block[2:].strip()
                    if q:
                        cards.append((q, a))
                        q = a = None
            if cards:
                for i, (q, a) in enumerate(cards, 1):
                    with st.expander(f"Flashcard {i}: {q}"):
                        st.markdown(f"**Answer:** {a}")
            else:
                st.info("Demo produced no structured flashcards; try rephrasing.")
        else:
            st.warning("Please enter topic/content.")

elif mode == "File Upload":
    st.subheader("📄 Upload PDF or DOCX")
    uploaded_file = st.file_uploader("Upload file", type=["pdf", "docx"])
    if uploaded_file and st.button("Process File", key="proc"):
        with st.spinner("Processing file..."):
            content = read_uploaded_file_to_text(uploaded_file)
            st.text_area("File content (preview)", content[:4000], height=300)
            summary = generate_response("Summarize this document for easier revision.", content)
        st.text_area("Document Summary", summary, height=250)

elif mode == "Exam Generator":
    st.subheader("🧪 Exam Generator (MCQs)")
    input_text = st.text_area("Enter topic or material for MCQs:")
    if st.button("Generate MCQs", key="mcq"):
        if input_text:
            with st.spinner("Generating MCQs..."):
                response = generate_response("Make 5 neat multiple-choice questions (A–D) with the correct answer marked clearly. Use clean formatting.", input_text)
            st.markdown(response.replace("**", "*"))
        else:
            st.warning("Please paste the material you want MCQs for.")
