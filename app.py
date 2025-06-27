import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import os
from src.ai_processor import ChapterProcessor
from src.human_review import  show_suggestions
from src.version_control import store_version
from src.db_inspector import display_versions 
from src.rl_search import RLSearchEngine



from dotenv import load_dotenv
load_dotenv()

# Constants
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
SCREENSHOT_DIR = Path("data/screenshots")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Book Workflow UI", layout="wide")
st.title("📘 Automated Book Publication Workflow")

# Sidebar Navigation
page = st.sidebar.radio("Select Task", [
    "Select Chapter", "Spin with AI", "Human Review & Edit",
    "View Stored Versions", "Semantic Search"
])

#session state
if "selected_chapter" not in st.session_state:
    st.session_state.selected_chapter = None

# 1-> Select Chapter from existing
if page == "Select Chapter":
    st.header("📂 Select Pre-Scraped Chapter")
    chapters = sorted([f.stem for f in RAW_DIR.glob("*.txt")])
    selected = st.selectbox("Choose a chapter:", chapters)

    if selected:
        st.session_state.selected_chapter = selected
        txt_path = RAW_DIR / f"{selected}.txt"
        screenshot_path = SCREENSHOT_DIR / f"{selected}.png"

        st.subheader(f"📄 Chapter Text: {selected}")
        if txt_path.exists():
            with open(txt_path, "r", encoding="utf-8") as f:
                st.text_area("Raw Text", f.read()[:2000], height=400)
        else:
            st.error("Text file not found.")

        st.subheader("🖼️ Screenshot")
        if screenshot_path.exists():
            st.image(screenshot_path, caption="Chapter Screenshot")
        else:
            st.warning("Screenshot not found.")

# 2->Spin with AI
elif page == "Spin with AI":
    st.header("🤖 Rewrite Chapter with AI")
    selected = st.session_state.get("selected_chapter")
    if selected:
        st.markdown(f"**Selected Chapter:** `{selected}`")
        txt_path = RAW_DIR / f"{selected}.txt"
        if txt_path.exists() and st.button("Spin Chapter with AI"):
            processor = ChapterProcessor(groq_api_key=GROQ_API_KEY)
            output_path = processor.process_chapter(str(txt_path))
            if output_path:
                with open(output_path, "r", encoding="utf-8") as f:
                    text = f.read()
                st.success("Chapter rewritten successfully!")
                st.session_state.spinned_file = output_path
                st.text_area("Spinned Output", text[:1000] + "...", height=300)
        else:
            st.warning("Selected chapter file not found.")
    else:
        st.warning("No chapter selected. Please go to 'Select Chapter' first.")

# 3->Human Review & Edit
elif page == "Human Review & Edit":
    st.header("✍️ Human Review and Editing")
    spinned_file = st.session_state.get("spinned_file")
    if spinned_file and Path(spinned_file).exists():
        with open(spinned_file, "r", encoding="utf-8") as f:
            ai_text = f.read()

        st.markdown(f"**Reviewing:** `{Path(spinned_file).name}`")
        edited_text = st.text_area("Edit or approve the AI-generated text:", ai_text, height=300)

        if st.button("Show AI Suggestions"):
            suggestions = show_suggestions(ai_text)
            for i, (vid, score, snippet) in enumerate(suggestions):
                st.markdown(f"**Suggestion {i+1}** | Score: `{score:.2f}`")
                st.code(snippet)

        if st.button("Save & Store Version"):
            human_file = Path(spinned_file).parent / f"HumanEdited_{Path(spinned_file).name}"
            with open(human_file, "w", encoding="utf-8") as f:
                f.write(edited_text)

            version_type = "human_approved" if edited_text == ai_text else "human_edited"
            store_version(
                text=edited_text,
                source_file=Path(spinned_file).name,
                version_type=version_type
            )
            st.success(f"Saved as {human_file.name} and stored in ChromaDB.")
    else:
        st.warning("No spinned file found. Please run AI Spin first.")

# 4-> View Stored Versions
elif page == "View Stored Versions":
    st.header("📑 Stored Chapter Versions")
    st.markdown("Recent versions stored in ChromaDB:")
    display_versions(limit=None)
    

# 5->Semantic Search
elif page == "Semantic Search":
    st.header("🔎 Search Versions by Query")
    query = st.text_input("Enter semantic query:", "strong character introduction")
    if st.button("Search Versions"):
        searcher = RLSearchEngine()
        results = searcher.search(query=query, top_k=3)
        for i, (vid, score, preview) in enumerate(results):
            st.markdown(f"### Result {i+1}")
            st.markdown(f"**ID**: `{vid}` | **Score**: `{score:.2f}`")
            st.code(preview)

st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 Built by Aniket")