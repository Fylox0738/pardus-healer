"""Uygulama teması (GTK CSS).

Açık ve koyu mod tek bir şablondan, renk paletleri değiştirilerek üretilir.
GTK CSS'i ``var()`` desteklemediği için renkler ``@@TOKEN@@`` yer tutucularıyla
gömülür.
"""

from __future__ import annotations

ACCENT = "#00a79d"

_LIGHT = {
    "BG": "#f4f6f9",
    "CARD_BG": "#ffffff",
    "CARD_BORDER": "#e1e8ed",
    "TITLE": "#1a2b4c",
    "BODY": "#4a5568",
    "MUTED": "#94a3b8",
    "SIDEBAR_BG": "#1a2b4c",
    "SIDEBAR_TXT": "#aabbcc",
    "SIDEBAR_HOVER": "rgba(255,255,255,0.08)",
    "SEP": "rgba(255,255,255,0.08)",
    "INSIGHT_BG": "#ffffff",
    "BANNER_BG": "#fef3cd",
    "BANNER_TXT": "#856404",
    "BANNER_BORDER": "#f0d77c",
    "TERM_BG": "#1e2124",
}

_DARK = {
    "BG": "#0f172a",
    "CARD_BG": "#1e293b",
    "CARD_BORDER": "#334155",
    "TITLE": "#e2e8f0",
    "BODY": "#94a3b8",
    "MUTED": "#64748b",
    "SIDEBAR_BG": "#0d1b2a",
    "SIDEBAR_TXT": "#8899aa",
    "SIDEBAR_HOVER": "rgba(255,255,255,0.06)",
    "SEP": "rgba(255,255,255,0.06)",
    "INSIGHT_BG": "#1e293b",
    "BANNER_BG": "#854d0e",
    "BANNER_TXT": "#fef3cd",
    "BANNER_BORDER": "#a16207",
    "TERM_BG": "#020617",
}

_TEMPLATE = """
window, .main-area { background-color: @@BG@@; }

/* ---- Splash ---- */
.splash-bg    { background-color: #0d1b2a; }
.splash-title { font-weight: 900; font-size: 32pt; color: @@ACCENT@@; }
.splash-sub   { font-size: 12pt; color: #8899aa; }

/* ---- Sidebar ---- */
.sidebar { background-color: @@SIDEBAR_BG@@; }
.sidebar-btn {
    background: transparent; color: @@SIDEBAR_TXT@@;
    font-weight: 600; font-size: 12pt; border: none;
    border-radius: 8px; padding: 12px 18px;
}
.sidebar-btn:hover { background: @@SIDEBAR_HOVER@@; color: #ffffff; }
.sidebar-btn-active {
    background: rgba(0,167,157,0.25); color: @@ACCENT@@;
    font-weight: 700; font-size: 12pt; border: none;
    border-radius: 8px; padding: 12px 18px;
}
.sidebar-brand { font-weight: 900; font-size: 16pt; color: @@ACCENT@@; }
.sidebar-tagline { font-size: 8.5pt; color: @@SIDEBAR_TXT@@; }
.sidebar-sep   { background-color: @@SEP@@; min-height: 1px; }

/* ---- Başlık ---- */
.page-title { font-weight: 800; font-size: 22pt; color: @@TITLE@@; }
.page-sub   { font-size: 11pt; color: @@BODY@@; }

/* ---- Kartlar ---- */
.card {
    background-color: @@CARD_BG@@; border-radius: 12px;
    padding: 14px 20px; margin: 4px 0px;
    border: 1px solid @@CARD_BORDER@@;
    transition: border-color 160ms ease, background-color 160ms ease;
}
.card:hover { border-color: @@ACCENT@@; }
.card-ok      { border-left: 4px solid #22c55e; }
.card-warn    { border-left: 4px solid #eab308; }
.card-fail    { border-left: 4px solid #ef4444; }
.card-wait    { border-left: 4px solid #94a3b8; }
.card-info-b  { border-left: 4px solid #3b82f6; }
.card-title   { font-weight: 700; font-size: 12.5pt; color: @@TITLE@@; }
.card-info    { font-size: 10.5pt; color: @@BODY@@; margin-top: 2px; }
.card-cat {
    font-size: 8pt; color: @@MUTED@@; font-weight: 700;
    border: 1px solid @@CARD_BORDER@@; border-radius: 20px;
    padding: 1px 8px;
}
.card-expander { color: @@MUTED@@; font-size: 10pt; }
.card-detail {
    font-size: 10pt; color: @@BODY@@;
    padding: 4px 12px 8px 0px;
}
.status-icon  { font-size: 20pt; }

/* ---- Canlı izleme çubukları ---- */
.meter-title { font-size: 10pt; color: @@BODY@@; font-weight: 600; }
.meter-value { font-size: 10pt; color: @@TITLE@@; font-weight: 800; }

/* ---- Sağlık skoru / dashboard ---- */
.score-big    { font-weight: 900; font-size: 46pt; color: @@ACCENT@@; }
.score-grade  { font-weight: 800; font-size: 15pt; }
.score-label  { font-size: 11pt; color: @@BODY@@; }
.dash-stat {
    background-color: @@CARD_BG@@; border: 1px solid @@CARD_BORDER@@;
    border-radius: 10px; padding: 14px 18px;
}
.dash-stat-num   { font-weight: 800; font-size: 22pt; color: @@TITLE@@; }
.dash-stat-label { font-size: 10pt; color: @@BODY@@; }

/* ---- İçgörü kartı ---- */
.insight {
    background-color: @@INSIGHT_BG@@; border: 1px solid @@CARD_BORDER@@;
    border-radius: 10px; padding: 14px 18px; margin: 5px 0px;
    border-left: 5px solid #eab308;
}
.insight-fail { border-left: 5px solid #ef4444; }
.insight-warn { border-left: 5px solid #eab308; }
.insight-title { font-weight: 700; font-size: 12pt; color: @@TITLE@@; }
.insight-msg   { font-size: 10.5pt; color: @@BODY@@; margin-top: 3px; }
.insight-prio {
    background: @@ACCENT@@; color: white; font-weight: 700;
    font-size: 9pt; border-radius: 10px; padding: 1px 8px;
}

/* ---- Butonlar ---- */
.fix-button {
    background: @@ACCENT@@; color: white; font-weight: bold;
    border-radius: 8px; padding: 8px 18px; border: none;
    transition: background 140ms ease, box-shadow 140ms ease;
}
.fix-button:hover { background: #00c2b6; box-shadow: 0 2px 10px rgba(0,167,157,0.4); }
.report-button {
    background: transparent; color: @@TITLE@@; font-weight: bold;
    border-radius: 8px; padding: 8px 18px;
    border: 1px solid @@CARD_BORDER@@;
    transition: border-color 140ms ease, color 140ms ease;
}
.report-button:hover { border-color: @@ACCENT@@; color: @@ACCENT@@; }
/* "Otomatik Onar" — dikkat çekici degrade */
.heal-button {
    background: linear-gradient(90deg, #00a79d, #22c55e);
    color: white; font-weight: bold;
    border-radius: 8px; padding: 8px 18px; border: none;
    transition: box-shadow 140ms ease;
}
.heal-button:hover { box-shadow: 0 3px 14px rgba(34,197,94,0.45); }

/* ---- Banner ---- */
.apt-banner {
    background-color: @@BANNER_BG@@; color: @@BANNER_TXT@@;
    font-weight: 600; font-size: 10.5pt; padding: 8px 16px;
    border-bottom: 1px solid @@BANNER_BORDER@@;
}

/* ---- Terminal ---- */
.terminal-title { font-weight: bold; font-size: 12.5pt; color: @@TITLE@@; margin-bottom: 4px; }
.terminal-view {
    background-color: @@TERM_BG@@; color: #d4d4d4;
    font-family: monospace; font-size: 11pt; padding: 14px;
    border-radius: 8px; border-left: 4px solid @@ACCENT@@;
}

/* ---- Ayarlar ---- */
.settings-section-title { font-weight: 700; font-size: 14pt; color: @@TITLE@@; margin-bottom: 6px; }
.settings-label { font-size: 11pt; color: @@BODY@@; }
"""


def _build(palette: dict) -> str:
    css = _TEMPLATE.replace("@@ACCENT@@", ACCENT)
    for key, val in palette.items():
        css = css.replace(f"@@{key}@@", val)
    return css


CSS_LIGHT = _build(_LIGHT)
CSS_DARK = _build(_DARK)


def get_css(dark: bool) -> bytes:
    return (CSS_DARK if dark else CSS_LIGHT).encode("utf-8")
