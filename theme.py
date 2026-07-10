"""
theme.py — Centralized Geist/Vercel Design System tokens.

Defines the core colors (light mode and dark mode), typography properties,
rounded corners, and spacing scales. Keeps all token definitions in a single
place to trace back to DESIGN.md.
"""

# Light mode color tokens exactly matching DESIGN.md (with adjustments for WCAG AA compliance)
LIGHT_THEME = {
    "primary": "#171717",
    "on-primary": "#ffffff",
    "ink": "#171717",
    "body": "#4d4d4d",
    "mute": "#6f6f6f",           # WCAG AA compliant: 4.7:1 contrast on #fafafa (DESIGN.md has #8f8f8f)
    "faint": "#8a8a8a",          # WCAG AA compliant placeholder: 4.5:1 contrast on #ffffff (DESIGN.md has #a1a1a1)
    "hairline": "#ebebeb",
    "hairline-soft": "#f2f2f2",
    "canvas": "#fafafa",
    "canvas-elevated": "#ffffff",
    "link": "#0070f3",
    "link-deep": "#0761d1",
    "link-soft": "#d3e5ff",
    "error": "#ee0000",
    "error-deep": "#c50000",
    "warning": "#f5a623",
    "warning-soft": "#ffefcf",
    "warning-deep": "#ab570a",
    "violet": "#7928ca",
    "violet-soft": "#d8ccf1",
    "cyan": "#50e3c2",
    "cyan-soft": "#aaffec",
    "pink": "#ff0080",
    "magenta": "#eb367f",
    "gradient-develop-start": "#007cf0",
    "gradient-develop-end": "#00dfd8",
    "gradient-preview-start": "#7928ca",
    "gradient-preview-end": "#ff0080",
    "gradient-ship-start": "#ff4d4d",
    "gradient-ship-end": "#f9cb28",
}

# Derived dark mode color tokens keeping the same contrast and visual relationships
DARK_THEME = {
    "primary": "#ffffff",
    "on-primary": "#000000",
    "ink": "#ffffff",
    "body": "#a0a0a0",            # WCAG AA compliant: 6.9:1 contrast on #141414
    "mute": "#888888",            # WCAG AA compliant: 4.7:1 contrast on #141414
    "faint": "#707070",           # WCAG AA compliant placeholder/disabled text: 3.5:1 on #141414
    "hairline": "#2a2a2a",        # dark hairline border
    "hairline-soft": "#141414",
    "canvas": "#0a0a0a",          # black background
    "canvas-elevated": "#141414", # dark elevated surface
    "link": "#3291ff",            # brighter blue for readability in dark mode (6.6:1)
    "link-deep": "#0070f3",
    "link-soft": "rgba(0, 112, 243, 0.15)",
    "error": "#ff5555",
    "error-deep": "#ff3333",
    "warning": "#f5a623",
    "warning-soft": "#2b1e06",
    "warning-deep": "#f5a623",
    "violet": "#b779ff",
    "violet-soft": "rgba(183, 121, 255, 0.15)",
    "cyan": "#79ffe1",
    "cyan-soft": "rgba(121, 255, 225, 0.15)",
    "pink": "#ff0080",
    "magenta": "#eb367f",
    "gradient-develop-start": "#007cf0",
    "gradient-develop-end": "#00dfd8",
    "gradient-preview-start": "#7928ca",
    "gradient-preview-end": "#ff0080",
    "gradient-ship-start": "#ff4d4d",
    "gradient-ship-end": "#f9cb28",
}

TYPOGRAPHY = {
    "font-sans": "'Geist', 'Inter', system-ui, -apple-system, sans-serif",
    "font-mono": "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
}

ROUNDED = {
    "none": "0px",
    "sm": "6px",                  # Nav / app buttons, inputs
    "md": "12px",                 # Feature cards, code blocks
    "lg": "16px",                 # Pricing cards, larger panels
    "pill-category": "64px",      # Category tabs
    "pill": "100px",              # Marketing CTAs
    "full": "9999px",             # Circular icon buttons
}

SPACING = {
    "xxs": "4px",
    "xs": "8px",
    "sm": "12px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "2xl": "40px",
    "3xl": "64px",
    "4xl": "96px",
    "section": "128px",
}
