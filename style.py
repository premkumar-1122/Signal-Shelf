"""
style.py — DESIGN.md CSS injection for the Signal Shelf dashboard.

Applies the Vercel/Geist-inspired design system: stark ink-on-canvas duet,
hairline-first depth, 6px square button discipline, and Geist typography.
Supports dynamic prefers-color-scheme light/dark modes.
"""

import streamlit as st

# Minimal Geist-aligned SVG icons (base64) used as input affordances.
_SEARCH_ICON_LIGHT = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmci"
    "IHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJv"
    "a2U9IiMxNzE3MTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2Ut"
    "bGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMSIgY3k9IjExIiByPSI3Ii8+PGxpbmUgeDE9IjIx"
    "IiB5MT0iMjEiIHgyPSIxNi42NSIgeTI9IjE2LjY1Ii8+PC9zdmc+"
)
_SEARCH_ICON_DARK = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmci"
    "IHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJv"
    "a2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2Ut"
    "bGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMSIgY3k9IjExIiByPSI3Ii8+PGxpbmUgeDE9IjIx"
    "IiB5MT0iMjEiIHgyPSIxNi42NSIgeTI9IjE2LjY1Ii8+PC9zdmc+"
)


def inject_css():
    """Inject the full CSS theme derived from DESIGN.md into the Streamlit app."""
    # Determine active theme type
    theme_type = "light"
    if hasattr(st, "context") and st.context.theme:
        theme_type = st.context.theme.get("type", "light")

    # Select color variables block based on theme type
    if theme_type == "dark":
        root_vars = """
        --primary:            #ffffff;
        --on-primary:         #000000;
        --ink:                #ffffff;
        --body-color:         #a0a0a0;     /* Audited for 6.9:1 contrast on #141414 elevated */
        --mute:               #888888;     /* Audited for 4.7:1 contrast on #141414 elevated */
        --faint:              #707070;     /* Placeholder text: 3.5:1 contrast */
        --hairline:           #2a2a2a;     /* Stark hairline borders */
        --hairline-soft:      #1f1f1f;
        --canvas:             #0a0a0a;     /* Pure dark canvas background */
        --canvas-elevated:    #141414;     /* Elevated dashboard surfaces */
        --link:               #3291ff;     /* High contrast link blue in dark mode (6.6:1) */
        --link-deep:          #0070f3;
        --link-soft:          rgba(0, 112, 243, 0.15);
        --error:              #ff5555;     /* Audited for readability in dark mode */
        --error-soft:         rgba(255, 85, 85, 0.12);
        --error-deep:         #ff3333;
        --warning:            #f5a623;
        --warning-soft:       #2b1e06;     /* Dark warning background */
        --warning-deep:       #f5a623;
        --violet:             #b779ff;
        --violet-soft:        rgba(183, 121, 255, 0.12);
        --cyan:               #79ffe1;
        --cyan-soft:          rgba(121, 255, 225, 0.12);
        """
    else:
        root_vars = """
        --primary:            #171717;
        --on-primary:         #ffffff;
        --ink:                #171717;
        --body-color:         #4d4d4d;
        --mute:               #6f6f6f;     /* Audited for 4.7:1 contrast on #fafafa canvas */
        --faint:              #8a8a8a;    /* Audited for 4.5:1 contrast on #ffffff elevated */
        --hairline:           #ebebeb;
        --hairline-soft:      #f2f2f2;
        --canvas:             #fafafa;
        --canvas-elevated:    #ffffff;
        --link:               #0070f3;
        --link-deep:          #0761d1;
        --link-soft:          #d3e5ff;
        --error:              #ee0000;
        --error-soft:         rgba(238, 0, 0, 0.08);
        --error-deep:         #c50000;
        --warning:            #f5a623;
        --warning-soft:       #ffefcf;
        --warning-deep:       #ab570a;
        --violet:             #7928ca;
        --violet-soft:        #f6f0ff;
        --cyan:               #50e3c2;
        --cyan-soft:          #aaffec;
        --pink:               #ff0080;
        --magenta:            #eb367f;
        """

    css_content = """
    <style>
    /* ── Google Fonts: Geist & Geist Mono ──────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100..900&family=Geist:wght@100..900&display=swap');

    /* ── Design System Tokens (from DESIGN.md) ──────────────────── */
    :root {
        [ROOT_VARS]

        /* Typography */
        --font-sans:          'Geist', 'Inter', system-ui, -apple-system, sans-serif;
        --font-mono:          'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

        /* Border Radius */
        --rounded-none:       0px;
        --rounded-sm:         6px;
        --rounded-md:         12px;
        --rounded-lg:         16px;
        --rounded-pill:       100px;
        --rounded-full:       9999px;

        /* Spacing */
        --spacing-xxs:        4px;
        --spacing-xs:         8px;
        --spacing-sm:         12px;
        --spacing-md:         16px;
        --spacing-lg:         24px;
        --spacing-xl:         32px;
        --spacing-2xl:        40px;
        --spacing-3xl:        64px;
        --spacing-4xl:        96px;
        --spacing-section:    128px;
    }

    /* ── Global Styles & Layout Reset ────────────────────────── */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: var(--font-sans) !important;
        color: var(--body-color) !important;
        background-color: var(--canvas) !important;
    }

    /* App container bg */
    [data-testid="stAppViewContainer"] {
        background-color: var(--canvas);
    }

    .stApp {
        background-color: var(--canvas);
    }

    /* Text selection */
    ::selection {
        background-color: var(--link-soft);
        color: var(--ink);
    }

    /* Headings styling */
    h1, h2, h3, h4, h5, h6 {
        color: var(--ink) !important;
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    /* ── Hero Section with Mesh Gradient ───────────────────────── */
    .hero-band {
        background: radial-gradient(at 0% 0%, var(--cyan-soft) 0px, transparent 50%),
                    radial-gradient(at 50% 0%, var(--link-soft) 0px, transparent 50%),
                    radial-gradient(at 100% 0%, var(--violet-soft) 0px, transparent 50%),
                    radial-gradient(at 100% 100%, rgba(235, 54, 127, 0.05) 0px, transparent 50%),
                    radial-gradient(at 0% 100%, var(--warning-soft) 0px, transparent 50%),
                    var(--canvas);
        padding: var(--spacing-xl) var(--spacing-lg);
        border-radius: var(--rounded-md);
        border: 1px solid var(--hairline);
        margin-bottom: var(--spacing-md);
        text-align: left;
    }

    .hero-title {
        font-family: var(--font-sans);
        font-weight: 600;
        font-size: 40px;
        line-height: 1.1;
        color: var(--ink);
        margin: 0 0 var(--spacing-xs) 0;
        letter-spacing: -2px;
    }

    .hero-title .accent {
        color: var(--link) !important;
        background: none !important;
        -webkit-text-fill-color: var(--link) !important;
    }

    .hero-tagline {
        font-family: var(--font-sans);
        font-size: 16px;
        font-weight: 400;
        line-height: 24px;
        color: var(--body-color);
        margin: 0 0 var(--spacing-xs) 0;
        max-width: 720px;
    }

    .hero-hint {
        font-family: var(--font-sans);
        font-size: 13px;
        font-weight: 400;
        line-height: 18px;
        color: var(--mute);
        margin: 0;
    }

    /* ── Stats Strip ─────────────────────────────────────────── */
    .stats-strip {
        display: flex;
        flex-wrap: wrap;
        gap: var(--spacing-md);
        margin-top: 0px;
        margin-bottom: var(--spacing-md);
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--canvas-elevated);
        border-radius: var(--rounded-md);
        border: 1px solid var(--hairline);
    }

    .stat-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        font-family: var(--font-sans);
        font-size: 13px;
        color: var(--body-color);
    }

    .stat-item .stat-value {
        font-family: var(--font-mono);
        font-weight: 600;
        color: var(--ink);
        font-size: 14px;
    }

    .stat-item .stat-label {
        font-weight: 400;
        color: var(--mute);
    }

    /* ── Sidebar styling ──────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--canvas) !important;
        border-right: 1px solid var(--hairline) !important;
    }

    /* Tighten vertical block layout in the sidebar to prevent large gaps */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0px !important;
    }

    /* Set uniform margin-bottom on sidebar widget containers */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="element-container"] {
        margin-bottom: var(--spacing-sm) !important; /* 12px default gap between label and control */
        margin-top: 0px !important;
    }

    /* Eyebrow headings for sidebar sections - reset margins, delegate to container spacing */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        font-family: var(--font-mono) !important;
        font-weight: 500 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--mute) !important;
        margin: 0px !important;
        border: none !important;
    }

    /* Sidebar divider - thin hairline, reset margin to delegate to container */
    [data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid var(--hairline) !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* ── Custom Entry Card wrappers inside Expander ──────────────── */
    .entry-card {
        background: transparent;
        padding: 0;
        margin-bottom: var(--spacing-xs);
        border: none;
    }

    .entry-card-header, .entry-card-meta, .entry-card-personas {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: var(--spacing-xs);
        margin-bottom: var(--spacing-xs);
    }

    .entry-card-personas {
        margin-bottom: 0;
    }

    /* ── Badge / Tag Components ───────────────────────────────── */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: var(--spacing-xxs);
        padding: 2px 8px;
        border-radius: var(--rounded-sm);
        font-family: var(--font-sans);
        font-size: 12px;
        font-weight: 500;
        line-height: 16px;
        white-space: nowrap;
        border: 1px solid var(--hairline);
    }

    /* Source / Newsletter is Primary (stark background) */
    .badge-newsletter {
        background: var(--primary);
        color: var(--on-primary);
        font-weight: 600;
        border-color: var(--primary);
    }

    /* Dates & Setup default */
    .badge-date {
        background: var(--hairline-soft);
        color: var(--body-color);
    }

    .badge-date-unknown {
        background: var(--warning-soft);
        color: var(--warning-deep);
        border-color: var(--warning-soft);
    }

    .badge-content-type {
        background: var(--canvas-elevated);
        color: var(--ink);
    }

    .badge-theme {
        background: var(--violet-soft);
        color: var(--violet);
        border-color: var(--violet-soft);
        font-weight: 600;
    }

    .badge-sponsored {
        background: var(--error-soft);
        color: var(--error);
        border-color: var(--error-soft);
        font-size: 11px;
        font-weight: 600;
    }

    .badge-setup {
        background: var(--hairline-soft);
        color: var(--body-color);
    }

    .badge-setup-instant {
        background: var(--cyan-soft);
        color: var(--ink);
        border-color: var(--cyan-soft);
    }

    .badge-setup-quick {
        background: var(--warning-soft);
        color: var(--warning-deep);
        border-color: var(--warning-soft);
    }

    .badge-setup-deep {
        background: var(--error-soft);
        color: var(--error);
        border-color: var(--error-soft);
    }

    .badge-persona {
        background: var(--hairline-soft);
        color: var(--body-color);
        font-size: 11px;
        font-weight: 400;
        padding: 1px 6px;
        border: none;
    }

    /* ── Results Bar & Messages ────────────────────────────────── */
    .results-bar {
        font-family: var(--font-mono) !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--mute) !important;
        margin-top: var(--spacing-sm) !important;
        margin-bottom: var(--spacing-sm) !important;
        padding: 0 var(--spacing-xxs) !important;
    }

    .results-bar .count {
        color: var(--ink) !important;
        font-weight: 600 !important;
    }

    /* Empty state messages */
    .no-results-msg {
        text-align: center;
        padding: var(--spacing-3xl) var(--spacing-lg);
        color: var(--mute);
        font-family: var(--font-sans);
        font-size: 16px;
        background-color: var(--canvas-elevated);
        border-radius: var(--rounded-md);
        border: 1px solid var(--hairline);
        margin-top: var(--spacing-md);
    }

    .pagination-text {
        text-align: center;
        padding-top: var(--spacing-xs);
        font-family: var(--font-sans);
        font-size: 14px;
        color: var(--mute);
    }

    .pagination-text b {
        color: var(--ink);
    }

    /* ── Streamlit Widget Overrides ───────────────────────────── */
    
    /* Buttons: App controls - 6px square */
    .stButton > button {
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: var(--rounded-sm) !important;
        font-family: var(--font-sans) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 6px 12px !important;
        min-height: 36px !important;
        line-height: 1.2 !important;
        transition: border-color 0.15s ease, background-color 0.15s ease !important;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.02) !important;
    }

    .stButton > button:hover {
        border-color: var(--mute) !important;
        background-color: var(--hairline-soft) !important;
        color: var(--ink) !important;
    }

    .stButton > button:active {
        background-color: var(--hairline) !important;
        border-color: var(--primary) !important;
    }

    .stButton > button:disabled {
        background-color: var(--canvas) !important;
        color: var(--faint) !important;
        border-color: var(--hairline-soft) !important;
        box-shadow: none !important;
    }

    /* Clear all filters button in sidebar (styled slightly darker for hierarchy) */
    [data-testid="stSidebar"] .stButton > button {
        background-color: var(--canvas) !important;
        width: 100%;
    }

    /* Inputs: Text Fields - 6px square default */
    .stTextInput > div > div > input {
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        border-radius: var(--rounded-sm) !important;
        font-family: var(--font-sans) !important;
        border: 1px solid var(--hairline) !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: var(--faint) !important;
        opacity: 1;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }

    /* Primary Search Input in the Main view: sized up for primary-search prominence */
    [data-testid="stMainView"] .stTextInput > div > div > input {
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        border-radius: var(--rounded-md) !important;
        border: 1px solid var(--hairline) !important;
        padding: 12px 18px 12px 46px !important;
        font-size: 16px !important;
        height: 48px !important;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.02) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
        [SEARCH_ICON_BG]
    }

    [data-testid="stMainView"] .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.04), 0 0 0 1px var(--primary) !important;
    }

    /* Inputs: Multiselect dropdowns */
    .stMultiSelect > div > div {
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        border-radius: var(--rounded-sm) !important;
        border: 1px solid var(--hairline) !important;
        font-family: var(--font-sans) !important;
        box-shadow: none !important;
    }

    .stMultiSelect > div > div:focus-within {
        border-color: var(--primary) !important;
    }

    /* Chips inside multiselect */
    .stMultiSelect div[data-baseweb="tag"] {
        background-color: var(--hairline-soft) !important;
        border-radius: var(--rounded-sm) !important;
        border: 1px solid var(--hairline) !important;
        color: var(--ink) !important;
    }

    .stMultiSelect div[data-baseweb="tag"] span {
        color: var(--ink) !important;
    }

    /* Portaled dropdown options / menus (BaseWeb) styling to match variables */
    div[data-baseweb="popover"] {
        background-color: var(--canvas-elevated) !important;
    }
    div[data-baseweb="popover"] ul {
        background-color: var(--canvas-elevated) !important;
        border: 1px solid var(--hairline) !important;
    }
    div[data-baseweb="popover"] li {
        color: var(--ink) !important;
        background-color: var(--canvas-elevated) !important;
        font-family: var(--font-sans) !important;
    }
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: var(--hairline) !important;
        color: var(--ink) !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: var(--hairline-soft) !important;
        color: var(--ink) !important;
    }

    /* Calendar picker portal theme styling */
    div[data-baseweb="calendar"] {
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        border: 1px solid var(--hairline) !important;
    }
    div[data-baseweb="calendar"] button {
        color: var(--ink) !important;
    }
    div[data-baseweb="calendar"] button:hover {
        background-color: var(--hairline-soft) !important;
    }

    /* Inputs: Selectbox */
    .stSelectbox > div > div {
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        border-radius: var(--rounded-sm) !important;
        border: 1px solid var(--hairline) !important;
        font-family: var(--font-sans) !important;
        box-shadow: none !important;
    }

    .stSelectbox > div > div:focus-within {
        border-color: var(--primary) !important;
    }

    /* Radio buttons */
    .stRadio div[role="radiogroup"] {
        gap: var(--spacing-sm) !important;
    }

    .stRadio label {
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
        color: var(--body-color) !important;
    }

    /* Toggles */
    .stToggle label {
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
        color: var(--body-color) !important;
    }

    /* Expanders: Styled as Feature Cards - 12px rounded, flat hairline style with hover Level 1 Whisper Shadow */
    details, .streamlit-expanderHeader {
        background-color: var(--canvas-elevated) !important;
        border-radius: var(--rounded-md) !important;
        border: 1px solid var(--hairline) !important;
        margin-bottom: var(--spacing-sm) !important;
        overflow: hidden !important;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.01) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }
    
    details:hover, .streamlit-expanderHeader:hover {
        border-color: var(--mute) !important;
        box-shadow: 0px 1px 1px rgba(0, 0, 0, 0.04) !important; /* Level 1 Whisper Shadow */
    }

    details > summary, .streamlit-expanderHeader {
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        background-color: var(--canvas-elevated) !important;
        color: var(--ink) !important;
        padding: var(--spacing-sm) var(--spacing-md) !important;
        cursor: pointer !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        border: none !important; /* Reset nested borders */
    }

    details > summary:hover, .streamlit-expanderHeader:hover {
        background-color: var(--hairline-soft) !important;
    }

    details[open] > summary {
        border-bottom: 1px solid var(--hairline) !important;
        border-radius: var(--rounded-md) var(--rounded-md) 0px 0px !important;
    }

    /* Expander Content Area */
    details > div, .streamlit-expanderContent {
        background-color: var(--canvas-elevated) !important;
        border-radius: 0px 0px var(--rounded-md) var(--rounded-md) !important;
        padding: var(--spacing-md) !important;
        font-family: var(--font-sans) !important;
        color: var(--body-color) !important;
        border: none !important;
    }

    /* Nested Markdown components inside expanders */
    details p, details li, .streamlit-expanderContent p, .streamlit-expanderContent li {
        font-size: 14px !important;
        line-height: 22px !important;
        color: var(--body-color) !important;
    }

    details h1, details h2, details h3, .streamlit-expanderContent h1, .streamlit-expanderContent h2, .streamlit-expanderContent h3 {
        font-size: 18px !important;
        margin-top: var(--spacing-md) !important;
        margin-bottom: var(--spacing-xs) !important;
        color: var(--ink) !important;
    }

    details code, .streamlit-expanderContent code {
        background-color: var(--hairline-soft) !important;
        color: var(--ink) !important;
        padding: 2px 6px !important;
        border-radius: var(--rounded-sm) !important;
        font-family: var(--font-mono) !important;
        font-size: 13px !important;
        border: 1px solid var(--hairline) !important;
    }

    details pre, .streamlit-expanderContent pre {
        background-color: var(--canvas) !important;
        border: 1px solid var(--hairline) !important;
        border-radius: var(--rounded-sm) !important;
        padding: var(--spacing-md) !important;
        overflow-x: auto !important;
        margin: var(--spacing-sm) 0 !important;
    }

    details pre code, .streamlit-expanderContent pre code {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        color: var(--ink) !important;
        font-family: var(--font-mono) !important;
        font-size: 13px !important;
    }

    /* ── Streamlit UI Elements to Hide ────────────────────────── */
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}

    /* Smoother scrolling */
    html {
        scroll-behavior: smooth;
    }

    /* ── Responsive adjustments ───────────────────────────────── */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 30px !important;
            letter-spacing: -1.2px !important;
        }
        .hero-band {
            padding: var(--spacing-md) var(--spacing-sm) !important;
        }
        .stats-strip {
            gap: var(--spacing-xs) !important;
        }
        .stat-item {
            font-size: 11px !important;
        }
    }
    </style>
    """

    search_icon_uri = _SEARCH_ICON_DARK if theme_type == "dark" else _SEARCH_ICON_LIGHT
    search_icon_bg = (
        f'background-image: url("{search_icon_uri}") !important;'
        f'background-repeat: no-repeat !important;'
        f'background-position: 16px center !important;'
        f'background-size: 18px 18px !important;'
    )

    css_content = css_content.replace("[SEARCH_ICON_BG]", search_icon_bg)
    st.markdown(css_content.replace("[ROOT_VARS]", root_vars), unsafe_allow_html=True)
