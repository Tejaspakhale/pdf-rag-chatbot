import os
import tempfile
import streamlit as st
from rag import index_pdf, answer, reset_collection

st.set_page_config(page_title="Chat with your PDF", page_icon="📄")
st.title("📄 Chat with your Document")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_file" not in st.session_state:
    st.session_state.indexed_file = None

# ---- Sidebar: upload and index ----
with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader("Choose a PDF", type="pdf")

    if uploaded and uploaded.name != st.session_state.indexed_file:
        with st.spinner("Reading and indexing your PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name
            try:
                reset_collection()
                n_chunks = index_pdf(tmp_path, name=uploaded.name)
            except Exception as e:
                n_chunks = 0
                st.error(f"Could not read this PDF: {e}")
            finally:
                os.remove(tmp_path)

        if n_chunks == 0:
            st.error("No text found. This may be a scanned PDF. Try another file.")
            st.session_state.indexed_file = None
        else:
            st.session_state.indexed_file = uploaded.name
            st.session_state.messages = []
            st.success(f"Indexed {n_chunks} chunks from {uploaded.name}")

# ---- Chat history ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.caption(f"Page {s['page']}")
                    st.write(s["text"][:300] + "...")

# ---- Chat input ----
if not st.session_state.indexed_file:
    st.info("Upload a PDF in the sidebar to get started.")
else:
    question = st.chat_input("Ask something about your document")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply, sources = answer(question)
                except Exception as e:
                    reply, sources = f"Something went wrong: {e}", []
            st.markdown(reply)
            if sources:
                with st.expander("Sources"):
                    for s in sources:
                        st.caption(f"Page {s['page']}")
                        st.write(s["text"][:300] + "...")

        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "sources": sources}
        )