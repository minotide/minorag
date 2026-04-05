"""Utilitários de renderização Markdown para o chat."""

import markdown as _md_lib

_MD_CSS = """\
<style>
code {
    background-color: #0d1117;
    color: #f0883e;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: monospace;
    font-size: 13px;
}
pre {
    background-color: #0d1117;
    border: 1px solid #30363d;
    padding: 10px 14px;
    border-radius: 6px;
    margin-top: 6px;
    margin-bottom: 6px;
}
pre code {
    background-color: transparent;
    color: #c9d1d9;
    padding: 0;
    border: none;
}
h1 { font-size: 18px; color: #e6edf3; }
h2 { font-size: 16px; color: #e6edf3; }
h3 { font-size: 14px; color: #e6edf3; }
a  { color: #58a6ff; }
blockquote {
    border-left: 3px solid #30363d;
    margin-left: 0;
    padding-left: 12px;
    color: #8b949e;
}
table { border-collapse: collapse; }
th, td { border: 1px solid #30363d; padding: 6px 12px; }
th { background-color: #21262d; }
</style>
"""


def render_md(text: str) -> str:
    html = _md_lib.markdown(
        text, extensions=["fenced_code", "tables", "nl2br"]
    )
    return _MD_CSS + html
