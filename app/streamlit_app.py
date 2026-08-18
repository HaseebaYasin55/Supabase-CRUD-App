from __future__ import annotations
import sys
import html
from pathlib import Path

import streamlit as st

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
    page_title="DocHub — Document Manager",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --dv-bg: #FAF9F6;
        --dv-surface: #FFFFFF;
        --dv-surface-2: #F4F2ED;
        --dv-border: #E7E3DA;
        --dv-border-strong: #D8D2C4;
        --dv-text: #2A2825;
        --dv-text-dim: #8B8579;
        --dv-accent: #D9653E;
        --dv-accent-hover: #C1512D;
        --dv-accent-soft: #FBE9E0;
        --dv-accent-soft-2: #FDF3EE;
        --dv-accent-text: #A6431F;
        --dv-danger: #C0463B;
        --dv-danger-soft: #FBEAE8;
        --dv-warning-soft: #FBF1DE;
        --dv-warning-text: #8A6A1F;
        --dv-radius: 12px;
        --dv-radius-sm: 8px;
        --dv-shadow-sm: 0 1px 2px rgba(42, 40, 37, 0.05);
    }

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

    .stApp { background-color: var(--dv-bg); }

    html, body, [class*="css"] { color: var(--dv-text); }

    #MainMenu, header, footer { visibility: hidden; }

    .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"] .block-container,
    section.main .block-container {
        padding: 2.2rem 3.5rem 3rem 3.5rem !important;
        max-width: 100% !important;
    }

    [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    /* ---------------- Sidebar ---------------- */
    section[data-testid="stSidebar"] {
        background-color: var(--dv-surface);
        border-right: 1px solid var(--dv-border);
    }
    section[data-testid="stSidebar"] > div { padding-top: 1.4rem; }

    .dv-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 4px 22px 4px;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--dv-text);
        letter-spacing: -0.01em;
    }
    .dv-brand-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 8px;
        background-color: var(--dv-accent);
        color: #FFFFFF;
        font-size: 0.95rem;
    }

    section[data-testid="stSidebar"] div.stButton {
        margin-bottom: 2px;
    }
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        text-align: left;
        justify-content: flex-start;
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: var(--dv-radius-sm);
        color: var(--dv-text-dim);
        font-weight: 500;
        font-size: 0.88rem;
        padding: 0.5rem 0.7rem;
        min-height: 0 !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.12s ease, color 0.12s ease;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: var(--dv-surface-2);
        color: var(--dv-text);
        border-color: transparent;
        transform: none !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: var(--dv-accent-soft);
        color: var(--dv-accent-text);
        border: 1px solid transparent;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover {
        background-color: var(--dv-accent-soft);
        color: var(--dv-accent-text);
    }

    .dv-sidebar-footer {
        margin-top: 10px;
        padding: 14px 4px 4px 4px;
        border-top: 1px solid var(--dv-border);
    }
    .dv-sidebar-storage {
        background-color: var(--dv-surface-2);
        border: 1px solid var(--dv-border);
        border-radius: var(--dv-radius-sm);
        padding: 10px 12px;
        margin-bottom: 12px;
    }
    .dv-sidebar-storage-label {
        font-size: 0.7rem;
        color: var(--dv-text-dim);
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .dv-sidebar-storage-bar {
        width: 100%;
        height: 5px;
        border-radius: 999px;
        background-color: var(--dv-border);
        overflow: hidden;
        margin-top: 7px;
    }
    .dv-sidebar-storage-bar-fill {
        height: 100%;
        background-color: var(--dv-accent);
        border-radius: 999px;
    }
    .dv-sidebar-user {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 4px;
    }
    .dv-avatar {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background-color: var(--dv-surface-2);
        color: var(--dv-text);
        font-weight: 700;
        font-size: 0.72rem;
        flex-shrink: 0;
        border: 1px solid var(--dv-border);
    }
    .dv-sidebar-user-name {
        font-size: 0.83rem;
        font-weight: 600;
        color: var(--dv-text);
        line-height: 1.2;
    }
    .dv-sidebar-user-sub {
        font-size: 0.71rem;
        color: var(--dv-text-dim);
        line-height: 1.2;
    }

    /* ---------------- Headings ---------------- */
    .dv-page-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--dv-text);
        margin-bottom: 3px;
        letter-spacing: -0.015em;
        padding-left: 2px;
    }
    .dv-page-subtitle {
        font-size: 0.9rem;
        color: var(--dv-text-dim);
        margin-bottom: 1.7rem;
        padding-left: 2px;
    }
    .dv-section-heading {
        font-size: 0.98rem;
        font-weight: 600;
        color: var(--dv-text);
        margin: 0 0 2px 0;
        padding-left: 2px;
    }
    .dv-section-sub {
        font-size: 0.8rem;
        color: var(--dv-text-dim);
        margin-bottom: 0.9rem;
        padding-left: 2px;
    }

    /* ---------------- Cards ---------------- */
    .dv-card {
        background-color: var(--dv-surface);
        border: 1px solid var(--dv-border);
        border-radius: var(--dv-radius);
        padding: 18px 20px;
        margin: 0;
        transition: border-color 0.15s ease;
    }
    .dv-card:hover { border-color: var(--dv-border-strong); }

    .dv-stat-label {
        font-size: 0.76rem;
        color: var(--dv-text-dim);
        margin-bottom: 8px;
        font-weight: 500;
    }
    .dv-stat-value {
        font-size: 1.55rem;
        font-weight: 700;
        color: var(--dv-text);
        letter-spacing: -0.01em;
    }

    /* ---------------- Document rows ---------------- */
    .dv-doc-row {
        background-color: var(--dv-surface);
        border: 1px solid var(--dv-border);
        border-radius: var(--dv-radius-sm);
        padding: 13px 16px;
        margin: 0 0 8px 0;
        transition: border-color 0.15s ease;
    }
    .dv-doc-row:hover {
        border-color: var(--dv-border-strong);
    }
    .dv-doc-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background-color: var(--dv-surface-2);
        font-size: 1rem;
        flex-shrink: 0;
    }
    .dv-doc-name {
        font-weight: 600;
        color: var(--dv-text);
        font-size: 0.9rem;
        word-break: break-word;
    }

    .dv-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 999px;
        background-color: var(--dv-accent-soft);
        color: var(--dv-accent-text);
        border: none;
        margin-top: 4px;
    }

    /* ---------------- Empty state ---------------- */
    .dv-empty {
        text-align: center;
        padding: 56px 20px;
        margin: 0;
        color: var(--dv-text-dim);
        background-color: var(--dv-surface);
        border: 1px dashed var(--dv-border-strong);
        border-radius: var(--dv-radius);
    }
    .dv-empty-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background-color: var(--dv-accent-soft);
        color: var(--dv-accent);
        font-size: 1.3rem;
        margin-bottom: 14px;
    }
    .dv-empty h3 {
        color: var(--dv-text);
        margin-bottom: 4px;
        font-size: 1rem;
        font-weight: 700;
    }

    .dv-muted { color: var(--dv-text-dim); font-size: 0.83rem; }

    /* =========================================================
       BUTTONS — flat, minimal, no gradients
       ========================================================= */

    div.stButton > button {
        min-height: 40px !important;
        border-radius: var(--dv-radius-sm) !important;
        border: 1px solid var(--dv-border-strong) !important;
        background: var(--dv-surface) !important;
        color: var(--dv-text) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
        transition: background-color 0.12s ease, border-color 0.12s ease, color 0.12s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    div.stButton > button > div,
    div.stButton > button > span {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
        line-height: 1 !important;
    }

    div.stButton > button:hover {
        border-color: var(--dv-text-dim) !important;
        background: var(--dv-surface-2) !important;
        color: var(--dv-text) !important;
        transform: none !important;
    }

    div.stButton > button:active {
        background: var(--dv-border) !important;
    }

    div.stButton > button[kind="primary"] {
        background: var(--dv-accent) !important;
        border: 1px solid var(--dv-accent) !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background: var(--dv-accent-hover) !important;
        border-color: var(--dv-accent-hover) !important;
        color: #FFFFFF !important;
        transform: none !important;
    }

    /* ---------------- Inputs ---------------- */

    div[data-testid="stTextInput"] {
        margin-top: 2px;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        color: var(--dv-text) !important;
        -webkit-text-fill-color: var(--dv-text) !important;
        background: var(--dv-surface) !important;
        border: 1px solid var(--dv-border-strong) !important;
        border-radius: var(--dv-radius-sm) !important;
        padding: 0.65rem 0.9rem !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease !important;
    }

    div[data-testid="stTextInput"] input {
        caret-color: var(--dv-accent) !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: var(--dv-text-dim) !important;
        -webkit-text-fill-color: var(--dv-text-dim) !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--dv-accent) !important;
        box-shadow: 0 0 0 3px var(--dv-accent-soft-2) !important;
        outline: none !important;
    }

    div[data-testid="stTextInput"] input:hover {
        border-color: var(--dv-border-strong) !important;
    }

    /* ---------------- Documents search + category filter bar ---------------- */

    div[data-testid="stTextInput"]:has(input[aria-label="Search documents"]) div[data-baseweb="base-input"],
    div[data-testid="stTextInput"]:has(input[aria-label="Search documents"]) div[data-baseweb="input"] {
        height: 44px !important;
        border-radius: var(--dv-radius-sm) !important;
        border: 1px solid var(--dv-border-strong) !important;
        background-color: var(--dv-surface) !important;
        box-shadow: none !important;
        overflow: hidden !important;
        transition: border-color 0.15s ease !important;
    }

    div[data-testid="stTextInput"]:has(input[aria-label="Search documents"]) div[data-baseweb="base-input"]:hover,
    div[data-testid="stTextInput"]:has(input[aria-label="Search documents"]) div[data-baseweb="input"]:hover {
        border-color: var(--dv-text-dim) !important;
    }

    div[data-testid="stTextInput"]:has(input[aria-label="Search documents"]) div[data-baseweb="base-input"]:focus-within,
    div[data-testid="stTextInput"]:has(input[aria-label="Search documents"]) div[data-baseweb="input"]:focus-within {
        border-color: var(--dv-accent) !important;
        box-shadow: 0 0 0 3px var(--dv-accent-soft-2) !important;
    }

    div[data-testid="stTextInput"] input[aria-label="Search documents"] {
        height: 100% !important;
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        padding: 0 1rem 0 2.6rem !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238B8579' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'%3E%3C/line%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: 16px center !important;
        background-size: 16px 16px !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] div[data-baseweb="menu"],
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] ul[role="listbox"],
    div[data-baseweb="popover"] div[role="listbox"] {
        background-color: var(--dv-surface) !important;
    }

    div[data-baseweb="popover"] div[data-baseweb="menu"] {
        border: 1px solid var(--dv-border) !important;
        border-radius: var(--dv-radius-sm) !important;
        box-shadow: 0 4px 14px rgba(42, 40, 37, 0.09) !important;
        padding: 4px !important;
        overflow: hidden !important;
    }

    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] div[role="option"],
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] [role="option"] * {
        background-color: var(--dv-surface) !important;
        color: var(--dv-text) !important;
        border-radius: 6px !important;
        font-size: 0.87rem !important;
    }

    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] div[role="option"]:hover {
        background-color: var(--dv-surface-2) !important;
        color: var(--dv-text) !important;
    }

    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] div[aria-selected="true"] {
        background-color: var(--dv-accent-soft) !important;
        color: var(--dv-accent-text) !important;
        font-weight: 600 !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        min-height: 44px !important;
        border-radius: var(--dv-radius-sm) !important;
        border: 1px solid var(--dv-border-strong) !important;
        background-color: var(--dv-surface) !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover {
        border-color: var(--dv-text-dim) !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: var(--dv-accent) !important;
        box-shadow: 0 0 0 3px var(--dv-accent-soft-2) !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child div,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
        color: var(--dv-text) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        opacity: 1 !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
        fill: var(--dv-text-dim) !important;
        color: var(--dv-text-dim) !important;
    }

    /* ---------------- File uploader (upload dropzone) ---------------- */

    [data-testid="stFileUploader"] {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }

    [data-testid="stFileUploader"] > label {
        display: none !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        width: 100% !important;
        max-width: 560px !important;
        min-height: 130px !important;
        margin: 0 auto !important;
        padding: 20px 28px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        box-sizing: border-box !important;
        border: 1.5px dashed var(--dv-border-strong) !important;
        border-radius: var(--dv-radius) !important;
        background: var(--dv-surface-2) !important;
        box-shadow: none !important;
        text-align: center !important;
        transition: border-color 0.15s ease, background-color 0.15s ease !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--dv-accent) !important;
        background: var(--dv-accent-soft-2) !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        gap: 8px !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] > div {
        width: auto !important;
        margin: 0 auto !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] svg {
        display: block !important;
        width: 26px !important;
        height: 26px !important;
        margin: 0 auto 2px auto !important;
        color: var(--dv-accent) !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] > div:last-child {
        display: block !important;
        color: var(--dv-text) !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: center !important;
        margin: 0 auto !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] small,
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        color: transparent !important;
        font-size: 0 !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] > div:last-child::before {
        content: "Drop your file here";
        display: block !important;
        color: var(--dv-text) !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: center !important;
        margin: 0 auto !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        display: block !important;
        margin: 0 auto !important;
        background-color: var(--dv-surface) !important;
        border: 1px solid var(--dv-border-strong) !important;
        color: var(--dv-text) !important;
        border-radius: var(--dv-radius-sm) !important;
        padding: 0.4rem 1.1rem !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        min-width: 120px !important;
        text-align: center !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: var(--dv-surface-2) !important;
        border-color: var(--dv-text-dim) !important;
    }

    [data-testid="stFileUploaderDropzone"] button * {
        color: var(--dv-text) !important;
    }

    .dv-upload-success {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--dv-accent-text);
        font-weight: 600;
        font-size: 0.9rem;
        margin-top: 16px;
    }

    /* ---------------- Alerts (success/error/warning) ---------------- */
    div[data-testid="stAlert"] {
        border-radius: var(--dv-radius-sm) !important;
        border: 1px solid var(--dv-accent-soft) !important;
        background-color: var(--dv-accent-soft-2) !important;
        box-shadow: none !important;
    }

    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] div,
    div[data-testid="stAlert"] span,
    div[data-testid="stAlert"] * {
        color: var(--dv-accent-text) !important;
        opacity: 1 !important;
    }

    div[data-testid="stAlert"] svg {
        fill: var(--dv-accent) !important;
        color: var(--dv-accent) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: var(--dv-radius) !important;
        border-color: var(--dv-border) !important;
        background-color: var(--dv-surface);
        box-shadow: none !important;
    }

    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
        width: 100% !important;
        max-width: 560px !important;
        margin: 12px auto 0 auto !important;
        color: var(--dv-text) !important;
    }

    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] * {
        color: var(--dv-text) !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileSize"],
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileSize"] * {
        color: var(--dv-text-dim) !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] svg {
        color: var(--dv-text-dim) !important;
        opacity: 1 !important;
    }

    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] span,
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] div {
        opacity: 1 !important;
    }

    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button {
        color: var(--dv-text-dim) !important;
        opacity: 1 !important;
    }

    .dv-upload-status {
        width: 100%;
        max-width: 560px;
        margin: 16px auto 0 auto;
        padding: 10px 14px;
        border-radius: var(--dv-radius-sm);
        background-color: var(--dv-accent-soft-2);
        color: var(--dv-accent-text);
        font-size: 0.83rem;
        font-weight: 500;
        text-align: center;
        box-sizing: border-box;
        border: 1px solid var(--dv-accent-soft);
    }

    .dv-upload-status-warning {
        background-color: var(--dv-warning-soft);
        color: var(--dv-warning-text);
        border-color: var(--dv-warning-soft);
    }

    .dv-delete-confirm {
        width: 100%;
        box-sizing: border-box;
        margin: 8px 0 14px 0;
        padding: 14px 16px;
        border-radius: var(--dv-radius-sm);
        background-color: var(--dv-danger-soft);
        border: 1px solid #EDD3D0;
        color: #7A2E26;
        font-size: 0.9rem;
        font-weight: 500;
        line-height: 1.5;
    }

    .dv-delete-confirm strong {
        color: #5F231D;
        font-weight: 700;
    }

    .dv-edit-heading {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--dv-text);
        padding: 10px 14px;
        margin-bottom: 16px;
        background-color: var(--dv-surface-2);
        border: 1px solid var(--dv-border);
        border-radius: var(--dv-radius-sm);
        word-break: break-word;
    }

    div[data-testid="stHorizontalBlock"] div.stButton > button {
        align-items: center !important;
        justify-content: center !important;
    }

    div[data-testid="stHorizontalBlock"] div.stButton > button span,
    div[data-testid="stHorizontalBlock"] div.stButton > button svg {
        vertical-align: middle !important;
        position: relative !important;
        top: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] div.stButton > button {
        letter-spacing: -0.005em !important;
    }

    div[data-testid="stDownloadButton"] > button {
        min-height: 40px !important;
        border-radius: var(--dv-radius-sm) !important;
        border: 1px solid var(--dv-border-strong) !important;
        background: var(--dv-surface) !important;
        color: var(--dv-text) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
        transition: background-color 0.12s ease, border-color 0.12s ease !important;
    }

    div[data-testid="stDownloadButton"] > button:hover {
        border-color: var(--dv-text-dim) !important;
        background: var(--dv-surface-2) !important;
        color: var(--dv-text) !important;
        transform: none !important;
    }

    div[data-testid="stDownloadButton"] > button:active,
    div[data-testid="stDownloadButton"] > button:focus,
    div[data-testid="stDownloadButton"] > button:focus-visible {
        background: var(--dv-border) !important;
        color: var(--dv-text) !important;
        border-color: var(--dv-border-strong) !important;
        outline: none !important;
        transform: none !important;
    }

    div[data-testid="stDownloadButton"] > button *,
    div[data-testid="stDownloadButton"] > button:active *,
    div[data-testid="stDownloadButton"] > button:focus *,
    div[data-testid="stDownloadButton"] > button:focus-visible * {
        color: var(--dv-text) !important;
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

NAV_ITEMS = [
    ("Dashboard", "", "Dashboard"),
    ("Documents", "", "Files"),
    ("Upload", "", "Add files"),
]

with st.sidebar:
    st.markdown(
        '<div class="dv-brand"><span class="dv-brand-icon">🗂️</span> DocHub</div>',
        unsafe_allow_html=True,
    )

    for page_key, icon, label in NAV_ITEMS:
        if st.button(
            f"{icon}  {label}",
            use_container_width=True,
            type="primary" if st.session_state.page == page_key else "secondary",
            key=f"nav_{page_key}",
        ):
            go_to(page_key)
            st.rerun()

    # Storage-used snapshot + user footer, styled to match the mockup's
    # bottom-of-sidebar block. Uses only real data already computed from
    # list_documents(); no new backend calls are introduced.
    footer_docs, footer_error = safe_list_documents()
    total_size_bytes = sum(d.file_size for d in footer_docs) if footer_docs else 0
    # Purely a visual capacity reference for the progress bar — cosmetic only,
    # does not reflect a real Supabase storage quota.
    display_cap_bytes = 5 * 1024 * 1024 * 1024  # 5 GB, for the bar's fill %
    used_pct = min(100, round((total_size_bytes / display_cap_bytes) * 100, 1)) if display_cap_bytes else 0

    st.markdown('<div class="dv-sidebar-footer">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="dv-sidebar-storage">
            <div class="dv-sidebar-storage-label">Storage used</div>
            <div style="font-weight:600; font-size:0.85rem; color:var(--dv-text);">
                {format_file_size(total_size_bytes)}
            </div>
            <div class="dv-sidebar-storage-bar">
                <div class="dv-sidebar-storage-bar-fill" style="width:{used_pct}%;"></div>
            </div>
        </div>
        <div class="dv-sidebar-user">
            <span class="dv-avatar">DH</span>
            <div>
                <div class="dv-sidebar-user-name">DocHub</div>
                <div class="dv-sidebar-user-sub">Supabase workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ======================================================================
# 4. PAGE RENDERERS
# ======================================================================


def render_page_header(title: str, subtitle: str, show_upload_cta: bool = False) -> None:
    if show_upload_cta:
        head_left, head_right = st.columns([4, 1], gap="large")
        with head_left:
            st.markdown(f'<div class="dv-page-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="dv-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)
        with head_right:
            if st.button("＋ Upload document", type="primary", use_container_width=True, key="cta_upload"):
                go_to("Upload")
                st.rerun()
    else:
        st.markdown(f'<div class="dv-page-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="dv-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_dashboard() -> None:
    render_page_header(
        "Overview",
        "A quick overview of your document workspace.",
    )

    docs, error = safe_list_documents()
    if error:
        st.error(f"Couldn't load dashboard data: {error}")
        return

    total_docs = len(docs)
    total_size = sum(d.file_size for d in docs)
    categories = {}
    for d in docs:
        categories[d.category] = categories.get(d.category, 0) + 1

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown(
            f'<div class="dv-card"><div class="dv-stat-label">Total documents</div>'
            f'<div class="dv-stat-value">{total_docs}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="dv-card"><div class="dv-stat-label">Storage used</div>'
            f'<div class="dv-stat-value">{format_file_size(total_size)}</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        top_category = max(categories, key=categories.get) if categories else "—"
        st.markdown(
            f'<div class="dv-card"><div class="dv-stat-label">Top category</div>'
            f'<div class="dv-stat-value">{top_category}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="dv-section-heading">Recent documents</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dv-section-sub">The latest files added to your workspace.</div>',
        unsafe_allow_html=True,
    )

    if not docs:
        render_empty_state()
        return

    for doc in docs[:5]:
        icon = get_file_icon(doc.file_name)
        st.markdown(
            f"""
            <div class="dv-doc-row">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:16px;">
                    <div style="display:flex; align-items:center; gap:12px; min-width:0;">
                        <span class="dv-doc-icon">{icon}</span>
                        <div style="min-width:0;">
                            <div class="dv-doc-name">{doc.file_name}</div>
                            <span class="dv-badge">{doc.category}</span>
                        </div>
                    </div>
                    <div class="dv-muted" style="white-space:nowrap;">{format_file_size(doc.file_size)} · {format_datetime(doc.uploaded_at)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state(
    heading: str = "No documents yet",
    body: str = "Upload your first document to start building your workspace.",
) -> None:
    st.markdown(
        f"""
        <div class="dv-empty">
            <div class="dv-empty-icon">🗂️</div>
            <h3>{heading}</h3>
            <p class="dv-muted">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("＋ Upload document", use_container_width=True, type="primary", key="empty_upload_cta"):
            go_to("Upload")
            st.rerun()


def render_documents() -> None:
    render_page_header(
        "Documents",
        "Browse, search, organize, and manage your uploaded documents.",
    )

    top_left, top_right = st.columns([3, 1], gap="medium")
    with top_left:
        search = st.text_input(
            "Search documents",
            placeholder="Search documents...",
            label_visibility="collapsed",
        )
    with top_right:
     selected_category = st.selectbox(
        "Category",
        ["All"] + CATEGORIES,
        label_visibility="collapsed",
    )

    category_filter = None if selected_category == "All" else selected_category

        

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    docs, error = safe_list_documents(category=category_filter)
    if error:
        st.error(f"Couldn't load documents: {error}")
        return

    if search:
        docs = [d for d in docs if search.lower() in d.file_name.lower()]

    if not docs:
        render_empty_state(
            "Your document workspace is empty",
            "Upload your first document and manage everything from one place.",
        )
        return

    for doc in docs:
        render_document_row(doc)


def render_document_row(doc) -> None:
    icon = get_file_icon(doc.file_name)
    with st.container():
        st.markdown('<div class="dv-doc-row">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6, c7 = st.columns(
         [0.45, 3.0, 1.0, 1.35, 1.15, 0.95, 0.95],
         gap="small",
)

        with c1:
            st.markdown(f"<span class='dv-doc-icon'>{icon}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='dv-doc-name'>{doc.file_name}</div>", unsafe_allow_html=True)
            if doc.description:
                st.markdown(f"<span class='dv-muted'>{doc.description}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='dv-badge'>{doc.category}</span>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<span class='dv-muted'>{format_file_size(doc.file_size)}</span>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<span class='dv-muted'>{format_datetime(doc.uploaded_at)}</span>", unsafe_allow_html=True)
        with c5:
          try:
             file_bytes = download_document(doc)

             st.download_button(
             label="↓  Download",
             data=file_bytes,
             file_name=doc.file_name,
             mime=doc.file_type,
             key=f"dl_{doc.id}",
             use_container_width=True,
        )
          except DocumentServiceError as exc:
           st.error(f"Download failed: {exc}")

        with c6:
          if st.button(
            "✎  Edit",
            key=f"edit_{doc.id}",
            use_container_width=True,
    ):
           st.session_state.editing_id = doc.id
           st.rerun()

        with c7:
          if st.button(
            "♢  Delete",
           key=f"del_{doc.id}",
           use_container_width=True,
    ):
           st.session_state.confirm_delete_id = doc.id
           st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.confirm_delete_id == doc.id:
        render_delete_confirmation(doc)

    if st.session_state.editing_id == doc.id:
        render_edit_panel(doc)





def render_delete_confirmation(doc) -> None:
    with st.container():
        st.markdown(
            f"<div class='dv-delete-confirm'>Delete <strong>{html.escape(doc.file_name)}</strong>? "
            "This permanently removes the file and its metadata.</div>",
            unsafe_allow_html=True,
        )
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
        st.markdown(
            f"<div class='dv-edit-heading'>Editing: {html.escape(doc.file_name)}</div>",
            unsafe_allow_html=True,
        )

        new_category = st.selectbox(
            "Category", CATEGORIES,
            index=CATEGORIES.index(doc.category) if doc.category in CATEGORIES else 0,
            key=f"cat_{doc.id}",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save metadata", key=f"save_{doc.id}", type="primary", use_container_width=True):
                try:
                    update_document_metadata(doc.id, description=doc.description, category=new_category)
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
            if st.button("Replace file", key=f"replace_btn_{doc.id}", type="primary"):
                with st.spinner("Uploading replacement and updating record..."):
                    try:
                        replace_document_file(doc.id, new_file.getvalue(), new_file.name)
                        st.success("File replaced successfully.")
                        st.session_state.editing_id = None
                        st.rerun()
                    except DocumentServiceError as exc:
                        st.error(f"Replace failed: {exc}")


def render_upload() -> None:
    render_page_header(
        "Upload document",
        "Add a document to your workspace. Files are validated securely before being stored.",
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
                 "Upload file",
            type=None,
            help="Max size depends on your .env MAX_FILE_SIZE_MB setting (default 20 MB).",
            label_visibility="collapsed",
)

        # Note: no visible file-preview row is shown once a file is chosen —
        # `uploaded_file` is still held by Streamlit's uploader state and is
        # passed straight into upload_document() below, so the upload
        # behavior is unchanged; only the extra preview card was removed.

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        # Description input removed from the UI per request. The
        # upload_document() call below still accepts a description, so we
        # simply pass an empty string — no backend behavior changes.
        description = ""
        _, cat_mid, _ = st.columns([1, 2, 1])
        with cat_mid:
          category = st.selectbox(
               "Category",
                CATEGORIES,
                index=None,
                placeholder="Select a category..."
    )
        # Upload status
        if uploaded_file is not None and category is None:
            st.markdown(
                 """
                 <div class="dv-upload-status dv-upload-status-warning">
                   Select a category to continue.
                 </div>
                 """,
                 unsafe_allow_html=True,
    )

        elif uploaded_file is not None and category is not None:
            st.markdown(
                   """
                    <div class="dv-upload-status">
                     ✓ Ready to upload
                    </div>
                   """,
                   unsafe_allow_html=True,
    )
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("＋ Upload document", type="primary", disabled=(uploaded_file is None or category is None)):
            with st.spinner("Validating with Edge Function and uploading..."):
                try:
                    doc = upload_document(
                        file_bytes=uploaded_file.getvalue(),
                        file_name=uploaded_file.name,
                        description=description,
                        category=category,
                    )
                    st.markdown(
                        "<div class='dv-upload-success'>✓ Document uploaded successfully.</div>"
                        f"<div class='dv-muted' style='margin-top:4px;'>Validation tag: <code>{doc.validation_tag}</code></div>",
                        unsafe_allow_html=True,
                    )
                except DocumentServiceError as exc:
                    st.error(f"Upload failed: {exc}")


# ======================================================================
# 5. ROUTER
# ======================================================================

PAGES = {
    "Dashboard": render_dashboard,
    "Documents": render_documents,
    "Upload": render_upload,
}

# If the app was left on a page that no longer exists (e.g. the removed
# Settings/About page) from a previous session, fall back to Dashboard.
if st.session_state.page not in PAGES:
    st.session_state.page = "Dashboard"

PAGES[st.session_state.page]()