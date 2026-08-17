"""
streamlit_app.py
==================
The modern, interactive UI for the Document Manager. Run with:

    streamlit run app/streamlit_app.py

This file is intentionally organized top-to-bottom like a real page:
  1. Page config + custom CSS ("theme")
  2. Session state setup
  3. Sidebar navigation
  4. Page renderers: Dashboard / Documents / Upload / Settings
  5. Router at the bottom

All actual Supabase logic lives in app/document_service.py — this file
is UI-only, which keeps it easy to read and easy to swap for a
different frontend later if you ever want to.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow running via `streamlit run app/streamlit_app.py` from repo root.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.document_service import (  # noqa: E402
    DocumentServiceError,
    delete_document,
    download_document,
    get_public_url,
    list_documents,
    replace_document_file,
    update_document_metadata,
    upload_document,
)
from app.utils import format_datetime, format_file_size, get_file_icon  # noqa: E402

# ======================================================================
# 1. PAGE CONFIG + THEME
# ======================================================================

st.set_page_config(
    page_title="DocVault — Document Manager",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    :root {
        --dv-bg: #0f1115;
        --dv-surface: #161922;
        --dv-surface-2: #1d212c;
        --dv-border: #2a2f3c;
        --dv-text: #e7e9ee;
        --dv-text-dim: #9aa0ae;
        --dv-accent: #6c8bff;
        --dv-accent-soft: rgba(108, 139, 255, 0.12);
        --dv-success: #4ade80;
        --dv-danger: #f87171;
        --dv-radius: 12px;
    }

    .stApp { background-color: var(--dv-bg); }

    /* Hide default Streamlit chrome for a cleaner "app" feel */
    #MainMenu, header, footer { visibility: hidden; }

    section[data-testid="stSidebar"] {
        background-color: var(--dv-surface);
        border-right: 1px solid var(--dv-border);
    }

    .dv-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0 20px 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--dv-text);
        border-bottom: 1px solid var(--dv-border);
        margin-bottom: 18px;
    }

    .dv-card {
        background-color: var(--dv-surface);
        border: 1px solid var(--dv-border);
        border-radius: var(--dv-radius);
        padding: 20px 22px;
        transition: border-color 0.15s ease, transform 0.15s ease;
    }
    .dv-card:hover { border-color: var(--dv-accent); }

    .dv-stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--dv-text-dim);
        margin-bottom: 6px;
    }
    .dv-stat-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: var(--dv-text);
    }

    .dv-doc-row {
        background-color: var(--dv-surface);
        border: 1px solid var(--dv-border);
        border-radius: var(--dv-radius);
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }
    .dv-doc-row:hover {
        border-color: var(--dv-accent);
        background-color: var(--dv-surface-2);
    }

    .dv-badge {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 999px;
        background-color: var(--dv-accent-soft);
        color: var(--dv-accent);
        border: 1px solid rgba(108, 139, 255, 0.35);
    }

    .dv-empty {
        text-align: center;
        padding: 70px 20px;
        color: var(--dv-text-dim);
        background-color: var(--dv-surface);
        border: 1px dashed var(--dv-border);
        border-radius: var(--dv-radius);
    }
    .dv-empty-icon { font-size: 3rem; margin-bottom: 10px; }

    .dv-muted { color: var(--dv-text-dim); font-size: 0.85rem; }

    div.stButton > button {
        border-radius: 8px;
        border: 1px solid var(--dv-border);
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        border-color: var(--dv-accent);
        color: var(--dv-accent);
    }
    div.stButton > button[kind="primary"] {
        background-color: var(--dv-accent);
        border-color: var(--dv-accent);
    }

    [data-testid="stFileUploaderDropzone"] {
        border-radius: var(--dv-radius);
        border: 1.5px dashed var(--dv-border);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

CATEGORIES = ["General", "Finance", "Legal", "HR", "Engineering", "Marketing", "Other"]

# ======================================================================
# 2. SESSION STATE
# ======================================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None


def go_to(page: str) -> None:
    st.session_state.page = page


def safe_list_documents(category: str | None = None):
    try:
        return list_documents(category=category), None
    except DocumentServiceError as exc:
        return [], str(exc)


# ======================================================================
# 3. SIDEBAR
# ======================================================================

with st.sidebar:
    st.markdown('<div class="dv-brand">🗂️ &nbsp;DocVault</div>', unsafe_allow_html=True)

    if st.button("📊 Dashboard", use_container_width=True,
                 type="primary" if st.session_state.page == "Dashboard" else "secondary"):
        go_to("Dashboard")
    if st.button("📁 Documents", use_container_width=True,
                 type="primary" if st.session_state.page == "Documents" else "secondary"):
        go_to("Documents")
    if st.button("⬆️ Upload Document", use_container_width=True,
                 type="primary" if st.session_state.page == "Upload" else "secondary"):
        go_to("Upload")
    if st.button("⚙️ Settings / About", use_container_width=True,
                 type="primary" if st.session_state.page == "Settings" else "secondary"):
        go_to("Settings")

    st.markdown("---")
    st.markdown(
        '<p class="dv-muted">Supabase-powered document management.<br>'
        "Database + Storage + Edge Functions.</p>",
        unsafe_allow_html=True,
    )

# ======================================================================
# 4. PAGE RENDERERS
# ======================================================================


def render_dashboard() -> None:
    st.title("Dashboard")
    st.caption("An overview of everything stored in your document vault.")

    docs, error = safe_list_documents()
    if error:
        st.error(f"Couldn't load dashboard data: {error}")
        return

    total_docs = len(docs)
    total_size = sum(d.file_size for d in docs)
    categories = {}
    for d in docs:
        categories[d.category] = categories.get(d.category, 0) + 1

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="dv-card"><div class="dv-stat-label">Total Documents</div>'
            f'<div class="dv-stat-value">{total_docs}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="dv-card"><div class="dv-stat-label">Total Storage Used</div>'
            f'<div class="dv-stat-value">{format_file_size(total_size)}</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        top_category = max(categories, key=categories.get) if categories else "—"
        st.markdown(
            f'<div class="dv-card"><div class="dv-stat-label">Top Category</div>'
            f'<div class="dv-stat-value">{top_category}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("###")
    st.subheader("Recent Uploads")

    if not docs:
        render_empty_state()
        return

    for doc in docs[:5]:
        icon = get_file_icon(doc.file_name)
        st.markdown(
            f"""
            <div class="dv-doc-row">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:1.2rem;">{icon}</span>
                        &nbsp;<strong>{doc.file_name}</strong>
                        &nbsp;<span class="dv-badge">{doc.category}</span>
                    </div>
                    <div class="dv-muted">{format_file_size(doc.file_size)} · {format_datetime(doc.uploaded_at)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="dv-empty">
            <div class="dv-empty-icon">📭</div>
            <h3>No documents yet</h3>
            <p class="dv-muted">Upload your first document to get started.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("###")
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("⬆️ Upload Document", use_container_width=True, type="primary"):
            go_to("Upload")
            st.rerun()


def render_documents() -> None:
    st.title("Documents")
    st.caption("Browse, edit, replace, and delete your uploaded files.")

    top_left, top_right = st.columns([3, 1])
    with top_left:
        search = st.text_input("🔍 Search by file name", placeholder="e.g. invoice.pdf")
    with top_right:
        category_filter = st.selectbox("Category", ["All"] + CATEGORIES)

    docs, error = safe_list_documents(category=category_filter)
    if error:
        st.error(f"Couldn't load documents: {error}")
        return

    if search:
        docs = [d for d in docs if search.lower() in d.file_name.lower()]

    if not docs:
        render_empty_state()
        return

    for doc in docs:
        render_document_row(doc)


def render_document_row(doc) -> None:
    icon = get_file_icon(doc.file_name)
    with st.container():
        st.markdown('<div class="dv-doc-row">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6 = st.columns([0.4, 3, 1.3, 1.1, 1.6, 1.6])

        with c1:
            st.markdown(f"<span style='font-size:1.4rem;'>{icon}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{doc.file_name}**")
            if doc.description:
                st.markdown(f"<span class='dv-muted'>{doc.description}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='dv-badge'>{doc.category}</span>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<span class='dv-muted'>{format_file_size(doc.file_size)}</span>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<span class='dv-muted'>{format_datetime(doc.uploaded_at)}</span>", unsafe_allow_html=True)
        with c5:
            if st.button("⬇️ Download", key=f"dl_{doc.id}", use_container_width=True):
                handle_download(doc)
            if st.button("✏️ Edit", key=f"edit_{doc.id}", use_container_width=True):
                st.session_state.editing_id = doc.id
                st.rerun()
        with c6:
            if st.button("🗑️ Delete", key=f"del_{doc.id}", use_container_width=True):
                st.session_state.confirm_delete_id = doc.id
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.confirm_delete_id == doc.id:
        render_delete_confirmation(doc)

    if st.session_state.editing_id == doc.id:
        render_edit_panel(doc)


def handle_download(doc) -> None:
    try:
        file_bytes = download_document(doc)
    except DocumentServiceError as exc:
        st.error(f"Download failed: {exc}")
        return
    st.download_button(
        label=f"Save {doc.file_name}",
        data=file_bytes,
        file_name=doc.file_name,
        mime=doc.file_type,
        key=f"savebtn_{doc.id}",
    )


def render_delete_confirmation(doc) -> None:
    with st.container():
        st.warning(f"⚠️ Delete **{doc.file_name}**? This permanently removes the file and its metadata.")
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if st.button("Yes, delete", key=f"confirm_del_{doc.id}", type="primary"):
                try:
                    delete_document(doc.id)
                    st.session_state.confirm_delete_id = None
                    st.success(f"Deleted '{doc.file_name}'.")
                    st.rerun()
                except DocumentServiceError as exc:
                    st.error(f"Delete failed: {exc}")
        with c2:
            if st.button("Cancel", key=f"cancel_del_{doc.id}"):
                st.session_state.confirm_delete_id = None
                st.rerun()


def render_edit_panel(doc) -> None:
    with st.container(border=True):
        st.markdown(f"**Editing: {doc.file_name}**")

        new_description = st.text_area("Description", value=doc.description or "", key=f"desc_{doc.id}")
        new_category = st.selectbox(
            "Category", CATEGORIES,
            index=CATEGORIES.index(doc.category) if doc.category in CATEGORIES else 0,
            key=f"cat_{doc.id}",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save metadata", key=f"save_{doc.id}", type="primary", use_container_width=True):
                try:
                    update_document_metadata(doc.id, description=new_description, category=new_category)
                    st.success("Metadata updated.")
                    st.session_state.editing_id = None
                    st.rerun()
                except DocumentServiceError as exc:
                    st.error(f"Update failed: {exc}")
        with c2:
            if st.button("Close", key=f"close_{doc.id}", use_container_width=True):
                st.session_state.editing_id = None
                st.rerun()

        st.markdown("---")
        st.markdown("**Replace file**")
        new_file = st.file_uploader(
            "Choose a replacement file", key=f"replace_upload_{doc.id}", label_visibility="collapsed"
        )
        if new_file is not None:
            if st.button("🔁 Replace file", key=f"replace_btn_{doc.id}", type="primary"):
                with st.spinner("Uploading replacement and updating record..."):
                    try:
                        replace_document_file(doc.id, new_file.getvalue(), new_file.name)
                        st.success("File replaced successfully.")
                        st.session_state.editing_id = None
                        st.rerun()
                    except DocumentServiceError as exc:
                        st.error(f"Replace failed: {exc}")


def render_upload() -> None:
    st.title("Upload Document")
    st.caption("Drag & drop a file, or click to browse. Validated server-side by an Edge Function.")

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Drop your file here",
            type=None,
            help="Max size depends on your .env MAX_FILE_SIZE_MB setting (default 20 MB).",
        )
        col1, col2 = st.columns(2)
        with col1:
            description = st.text_area("Description (optional)", placeholder="e.g. Signed vendor contract")
        with col2:
            category = st.selectbox("Category", CATEGORIES)

        if uploaded_file is not None:
            st.markdown(
                f"<span class='dv-muted'>Selected: <strong>{uploaded_file.name}</strong> "
                f"({format_file_size(uploaded_file.size)})</span>",
                unsafe_allow_html=True,
            )

        if st.button("⬆️ Upload Document", type="primary", disabled=uploaded_file is None):
            with st.spinner("Validating with Edge Function and uploading..."):
                try:
                    doc = upload_document(
                        file_bytes=uploaded_file.getvalue(),
                        file_name=uploaded_file.name,
                        description=description,
                        category=category,
                    )
                    st.success(f"✅ '{doc.file_name}' uploaded successfully!")
                    st.markdown(
                        f"<span class='dv-muted'>Validation tag: <code>{doc.validation_tag}</code></span>",
                        unsafe_allow_html=True,
                    )
                except DocumentServiceError as exc:
                    st.error(f"❌ Upload failed: {exc}")


def render_settings() -> None:
    st.title("Settings / About")

    st.subheader("About this project")
    st.write(
        "DocVault is a Document Management CRUD application built to demonstrate "
        "Supabase PostgreSQL, Supabase Storage, and Supabase Edge Functions working "
        "together from a Python backend."
    )

    st.subheader("Architecture")
    st.code(
        "User -> Streamlit UI -> Python (document_service.py) -> Supabase\n"
        "                                                          ├── PostgreSQL (metadata)\n"
        "                                                          ├── Storage (files)\n"
        "                                                          └── Edge Function (validation)",
        language="text",
    )

    st.subheader("Learn more")
    st.write(
        "See **README.md** for setup instructions and **SUPABASE_GUIDE.md** for a "
        "complete beginner's explanation of every concept used in this project."
    )


# ======================================================================
# 5. ROUTER
# ======================================================================

PAGES = {
    "Dashboard": render_dashboard,
    "Documents": render_documents,
    "Upload": render_upload,
    "Settings": render_settings,
}

PAGES[st.session_state.page]()
