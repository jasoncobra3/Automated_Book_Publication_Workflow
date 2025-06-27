from src.version_control import client
import logging
import streamlit as st
import tempfile
import os


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def display_versions(limit: int = None):
    """"Display stored versions from ChromaDB."""
    try:
        collection = client.get_collection("book_versions")
        versions = collection.get()

        st.info(f"Found {len(versions['ids'])} versions.")

        if not versions['ids']:
            st.warning("No versions found in ChromaDB.")
            return

        #  data for version control
        for i, (vid, doc, meta) in enumerate(zip(
            reversed(versions['ids']),
            reversed(versions['documents']),
            reversed(versions['metadatas'])
        )):
            if limit and i >= limit:
                break

            with st.expander(f"📝 Version ID: {vid}"):
                st.markdown(f"**Type:** {meta.get('type', 'unknown')}")
                st.markdown(f"**Source:** {meta.get('source', 'N/A')}")
                st.markdown(f"**Words:** {meta.get('length', 0)}")
                st.code(doc[:500] + ("..." if len(doc) > 500 else ""), language='text')

                # Download button
                with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as tmp_file:
                    tmp_file.write(doc)
                    tmp_file_path = tmp_file.name
                st.download_button(
                    label="📥 Download .txt",
                    data=open(tmp_file_path, "rb").read(),
                    file_name=f"{vid}.txt",
                    mime="text/plain"
                )
                os.unlink(tmp_file_path)

                # Delete button
                if st.button(f"🗑️ Delete Version {vid}"):
                    collection.delete(ids=[vid])
                    st.warning(f"Version {vid} deleted. Please refresh the page.")

    except Exception as e:
        st.error(f"Error retrieving versions: {e}")

