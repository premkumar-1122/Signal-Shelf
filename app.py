"""
app.py — Signal Shelf: AI Newsletters Actionable Implementation Dashboard.

Entry point for the Streamlit application.
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import date

from data_loader import get_db, query_entries, get_filter_options, get_stats
from ui_components import render_hero, render_stats, render_results, render_pagination
from style import inject_css

# ─── Page Config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Signal Shelf — AI Newsletter Tips Database",
    page_icon="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iNiIgZmlsbD0iIzE3MTcxNyIvPjxnIGZpbGw9IiNmYWZhZmEiPjxyZWN0IHg9IjgiIHk9IjEyIiB3aWR0aD0iMTYiIGhlaWdodD0iMi41IiByeD0iMS4yNSIvPjxyZWN0IHg9IjgiIHk9IjE3IiB3aWR0aD0iMTEiIGhlaWdodD0iMi41IiByeD0iMS4yNSIvPjxyZWN0IHg9IjgiIHk9IjIyIiB3aWR0aD0iMTQiIGhlaWdodD0iMi41IiByeD0iMS4yNSIvPjwvZz48L3N2Zz4=",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Auto-refresh Config (Optional) ──────────────────────────────────────
if "auto_refresh" not in st.session_state:
    st.session_state["auto_refresh"] = False

if st.session_state["auto_refresh"]:
    st_autorefresh(interval=30000, limit=None, key="jsonl_watcher")

# ─── Inject CSS ──────────────────────────────────────────────────────────
inject_css()

# ─── Load Data ───────────────────────────────────────────────────────────
con, fts_available = get_db()
stats = get_stats(con)
options = get_filter_options(con)

# ─── Initialize Filter Session State Defaults ────────────────────────────
if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""
if "filter_newsletters" not in st.session_state:
    st.session_state["filter_newsletters"] = []
if "date_filter_mode" not in st.session_state:
    st.session_state["date_filter_mode"] = "Date Range"
if "filter_date_range" not in st.session_state:
    if options["date_min"] and options["date_max"]:
        st.session_state["filter_date_range"] = (options["date_min"], options["date_max"])
    else:
        st.session_state["filter_date_range"] = None
if "filter_single_date" not in st.session_state:
    st.session_state["filter_single_date"] = options["date_max"]
if "include_unknown" not in st.session_state:
    st.session_state["include_unknown"] = True
if "filter_content_types" not in st.session_state:
    st.session_state["filter_content_types"] = []
if "filter_themes" not in st.session_state:
    st.session_state["filter_themes"] = []
if "filter_sponsored" not in st.session_state:
    st.session_state["filter_sponsored"] = "All"
if "filter_personas" not in st.session_state:
    st.session_state["filter_personas"] = []
if "filter_setup_times" not in st.session_state:
    st.session_state["filter_setup_times"] = []
if "sort_by" not in st.session_state:
    st.session_state["sort_by"] = "Date (Newest First)"

# ─── Hero Section ────────────────────────────────────────────────────────
render_hero()
render_stats(stats)

# ─── Primary Search Bar ──────────────────────────────────────────────────
search_term = st.text_input(
    "Search content, themes, types...",
    placeholder="Search by keywords, themes, tools, or content types...",
    key="search_input",
    label_visibility="collapsed",
)

# ─── Sidebar: Filters ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Active Controls")

    # Surface a warning if MotherDuck connection failed
    if st.session_state.get("motherduck_connection_error"):
        st.warning(st.session_state["motherduck_connection_error"])

    # Surface any ingestion errors detected during JSONL loading
    if st.session_state.get("ingestion_errors"):
        with st.expander("Ingestion Warnings", expanded=True):
            st.error("Some JSONL lines were malformed and skipped:")
            for err in st.session_state["ingestion_errors"]:
                st.caption(err)

    if st.button("Clear All Filters", use_container_width=True):
        st.session_state["search_input"] = ""
        st.session_state["filter_newsletters"] = []
        st.session_state["date_filter_mode"] = "Date Range"
        if options["date_min"] and options["date_max"]:
            st.session_state["filter_date_range"] = (options["date_min"], options["date_max"])
        st.session_state["filter_single_date"] = options["date_max"]
        st.session_state["include_unknown"] = True
        st.session_state["filter_content_types"] = []
        st.session_state["filter_themes"] = []
        st.session_state["filter_sponsored"] = "All"
        st.session_state["filter_personas"] = []
        st.session_state["filter_setup_times"] = []
        st.session_state["sort_by"] = "Date (Newest First)"
        st.session_state["current_page"] = 1
        st.rerun()

    st.markdown("---")
    st.markdown("### Source Newsletter")
    selected_newsletters = st.multiselect(
        "Filter by newsletter",
        options=options["newsletters"],
        key="filter_newsletters",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Date Filter Mode")
    date_filter_mode = st.radio(
        "Date filter mode",
        options=["Date Range", "Single Date"],
        key="date_filter_mode",
        label_visibility="collapsed",
        horizontal=True,
    )

    date_min = options["date_min"]
    date_max = options["date_max"]
    date_range = None
    single_date = None

    if date_filter_mode == "Date Range":
        if date_min and date_max:
            date_range = st.date_input(
                "Select date range",
                min_value=date_min,
                max_value=date_max,
                key="filter_date_range",
                label_visibility="collapsed",
            )
    else:
        if date_max:
            single_date = st.date_input(
                "Select single date",
                min_value=date_min,
                max_value=date_max,
                key="filter_single_date",
                label_visibility="collapsed",
            )

    include_unknown_dates = st.toggle(
        "Include unknown dates",
        key="include_unknown",
        help="Show entries where the publication date is unknown or unparseable",
    )

    st.markdown("---")
    st.markdown("### Content Type")
    selected_content_types = st.multiselect(
        "Filter by content type",
        options=options["content_types"],
        key="filter_content_types",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Theme")
    selected_themes = st.multiselect(
        "Filter by theme",
        options=options["themes"],
        key="filter_themes",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Sponsored Content")
    sponsored_filter = st.radio(
        "Sponsored filter",
        options=["All", "Hide Sponsored", "Sponsored Only"],
        key="filter_sponsored",
        label_visibility="collapsed",
        horizontal=True,
    )

    st.markdown("---")
    st.markdown("### Target Persona")
    selected_personas = st.multiselect(
        "Filter by persona",
        options=options["persona_tags"],
        key="filter_personas",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Setup Time")
    selected_setup_times = st.multiselect(
        "Filter by setup time",
        options=options["setup_times"],
        key="filter_setup_times",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Sort By")
    sort_by = st.selectbox(
        "Sort order",
        options=[
            "Date (Newest First)",
            "Date (Oldest First)",
            "Newsletter A → Z",
            "Setup Time (Quickest)",
            "Setup Time (Most Involved)",
        ],
        key="sort_by",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Settings")
    st.checkbox(
        "Enable auto-refresh",
        key="auto_refresh",
        help="Automatically refresh the dashboard every 30 seconds to fetch updates from the database."
    )

# ─── Normalize date_range/single_date for the query ──────────────────────
query_date_range = None
if date_filter_mode == "Date Range" and date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    query_date_range = (date_range[0], date_range[1])

query_single_date = None
if date_filter_mode == "Single Date" and single_date:
    query_single_date = single_date

# ─── Query ───────────────────────────────────────────────────────────────
results_df = query_entries(
    con=con,
    fts_available=fts_available,
    search_term=search_term,
    newsletters=selected_newsletters or None,
    date_range=query_date_range,
    single_date=query_single_date,
    include_unknown_dates=include_unknown_dates,
    content_types=selected_content_types or None,
    themes=selected_themes or None,
    sponsored_filter=sponsored_filter,
    persona_tags=selected_personas or None,
    setup_times=selected_setup_times or None,
    sort_by=sort_by,
)

# ─── Pagination State ───────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# Reset to page 1 when filters change
filter_fingerprint = (
    search_term,
    tuple(selected_newsletters),
    date_filter_mode,
    str(query_date_range),
    str(query_single_date),
    include_unknown_dates,
    tuple(selected_content_types),
    tuple(selected_themes),
    sponsored_filter,
    tuple(selected_personas),
    tuple(selected_setup_times),
    sort_by,
)
if "last_filter_fingerprint" not in st.session_state:
    st.session_state.last_filter_fingerprint = filter_fingerprint

if st.session_state.last_filter_fingerprint != filter_fingerprint:
    st.session_state.current_page = 1
    st.session_state.last_filter_fingerprint = filter_fingerprint

# ─── Display Results ─────────────────────────────────────────────────────
if len(results_df) == 0:
    st.markdown(
        '<div class="no-results-msg">'
        'No entries match your current filters. Try broadening your search.'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    total_pages = render_results(
        results_df,
        page=st.session_state.current_page,
        per_page=15,
    )

    # Pagination controls
    new_page = render_pagination(st.session_state.current_page, total_pages)
    if new_page != st.session_state.current_page:
        st.session_state.current_page = new_page
        st.rerun()
