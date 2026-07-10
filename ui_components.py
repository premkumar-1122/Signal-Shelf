"""
ui_components.py — Reusable Streamlit UI components for Signal Shelf.

Hero section, entry cards, badge rendering, pagination controls.
All styled to match DESIGN.md tokens.
"""

import re
import streamlit as st
import pandas as pd
from datetime import date


# ─── Hero Section ─────────────────────────────────────────────────────────

def render_hero():
    """Render the hero banner with title and description."""
    st.markdown(f"""<div class="hero-band">
<div class="hero-title">
<span class="accent">Signal</span> Shelf
</div>
<p class="hero-tagline">
A living, searchable collection of concrete AI tips, tools, prompts &amp; workflows — pulled from top newsletters and ready to put to work.
</p>
<p class="hero-hint">
Search by keyword &nbsp;·&nbsp; Filter by newsletter, theme, or persona &nbsp;·&nbsp; Click any card to read the full guide
</p>
</div>""", unsafe_allow_html=True)


def render_stats(stats: dict):
    """Render the live stats in its own distinct band."""
    st.markdown(f"""<div class="stats-strip">
<div class="stat-item">
<span class="stat-value">{stats['total_entries']}</span>
<span class="stat-label">entries</span>
</div>
<div class="stat-item">
<span class="stat-value">{stats['total_sources']}</span>
<span class="stat-label">sources</span>
</div>
<div class="stat-item">
<span class="stat-value">{stats['total_themes']}</span>
<span class="stat-label">themes</span>
</div>
<div class="stat-item">
<span class="stat-label">Updated {stats['last_updated']}</span>
</div>
</div>""", unsafe_allow_html=True)


# ─── Badge Helpers ────────────────────────────────────────────────────────

def _badge(text: str, css_class: str) -> str:
    """Return an HTML badge span."""
    return f'<span class="badge {css_class}">{text}</span>'


def _setup_badge(setup_time: str) -> str:
    """Return a setup-time badge with semantic coloring."""
    if "Instant" in setup_time:
        return _badge(f"{setup_time}", "badge-setup-instant")
    elif "Quick" in setup_time:
        return _badge(f"{setup_time}", "badge-setup-quick")
    elif "Deep" in setup_time:
        return _badge(f"{setup_time}", "badge-setup-deep")
    return _badge(setup_time, "badge-setup")


def _date_badge(row) -> str:
    """Return a date badge or 'Date unknown' badge."""
    if row.get("is_date_known") and row.get("parsed_date"):
        d = row["parsed_date"]
        if isinstance(d, date):
            label = d.strftime("%b %d, %Y")
        else:
            label = str(d)
        return _badge(f"{label}", "badge-date")
    else:
        raw = row.get("date_raw", "unknown")
        if raw and raw.lower() != "unknown":
            return _badge(f"{raw}", "badge-date-unknown")
        return _badge("Date unknown", "badge-date-unknown")


# ─── Entry Card ───────────────────────────────────────────────────────────

def render_entry_card(row: dict, index: int):
    """Render a single entry as an expandable card."""
    # Build header badges
    nls = row.get("source_newsletters", [])
    if isinstance(nls, str):
        nls = [t.strip().strip("'\"") for t in nls.strip("[]").split(",") if t.strip()]
    newsletter_badges = "".join(
        _badge(nl, "badge-newsletter") for nl in nls if nl
    )
    date_b = _date_badge(row)
    content_type_badge = _badge(row["content_type"], "badge-content-type")
    theme_badge = _badge(row["theme"], "badge-theme")
    setup_badge = _setup_badge(row["setup_time"])

    sponsored_html = ""
    if row.get("sponsored"):
        sponsored_html = _badge("Sponsored", "badge-sponsored")

    # Persona pills
    persona_tags = row.get("persona_tags", [])
    if isinstance(persona_tags, str):
        # Handle if DuckDB returns as string representation
        persona_tags = [t.strip().strip("'\"") for t in persona_tags.strip("[]").split(",") if t.strip()]
    persona_pills = "".join(
        _badge(tag, "badge-persona") for tag in persona_tags if tag
    )

    # Content rendering
    raw_content = row.get("extracted_content", "")

    # Build the card header HTML — NO indentation to avoid Markdown code block
    card_header_html = f"""<div class="entry-card">
<div class="entry-card-header">
{newsletter_badges}
{date_b}
{content_type_badge}
</div>
<div class="entry-card-meta">
{theme_badge}
{setup_badge}
{sponsored_html}
</div>
<div class="entry-card-personas">
{persona_pills}
</div>
</div>"""

    # Use Streamlit expander for the content body
    # Extract the title from the first line of raw text to ensure no glued words or raw HTML
    title_preview = "Entry"
    if raw_content:
        first_line = raw_content.split('\n')[0].strip()
        # Remove markdown heading prefix
        first_line = re.sub(r'^#+\s+', '', first_line)
        # Remove bold/italic markers
        first_line = first_line.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
        title_preview = first_line

    if len(title_preview) > 80:
        title_preview = title_preview[:77] + "..."

    with st.expander(f"**{title_preview}**", expanded=False):
        st.markdown(card_header_html, unsafe_allow_html=True)
        st.markdown(raw_content, unsafe_allow_html=False)


# ─── Results Display ──────────────────────────────────────────────────────

def render_results(df: pd.DataFrame, page: int = 1, per_page: int = 15):
    """
    Render paginated result cards from a DataFrame.
    Returns total pages for pagination controls.
    """
    total = len(df)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)

    # Results count bar
    st.markdown(
        f'<div class="results-bar">'
        f'Showing <span class="count">{start_idx + 1}–{end_idx}</span> of '
        f'<span class="count">{total}</span> entries'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Render cards
    page_df = df.iloc[start_idx:end_idx]
    for i, (_, row) in enumerate(page_df.iterrows()):
        render_entry_card(row.to_dict(), start_idx + i)

    return total_pages


def render_pagination(current_page: int, total_pages: int):
    """Render pagination controls."""
    if total_pages <= 1:
        return current_page

    cols = st.columns([1, 1, 2, 1, 1])

    with cols[0]:
        if st.button("First", disabled=(current_page <= 1), key="page_first"):
            return 1
    with cols[1]:
        if st.button("‹ Prev", disabled=(current_page <= 1), key="page_prev"):
            return current_page - 1
    with cols[2]:
        st.markdown(
            f'<div class="pagination-text">'
            f'Page <b>{current_page}</b> of <b>{total_pages}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with cols[3]:
        if st.button("Next ›", disabled=(current_page >= total_pages), key="page_next"):
            return current_page + 1
    with cols[4]:
        if st.button("Last", disabled=(current_page >= total_pages), key="page_last"):
            return total_pages

    return current_page
