#!/usr/bin/env python3
"""
Convert Academic Markdown Paper to PDF / HTML.

Supports multiple conversion backends with graceful fallback:
1. pandoc (with xelatex / pdflatex / weasyprint)
2. WeasyPrint CLI
3. Headless Chrome / Chromium / Edge
4. HTML preview file generation (printable directly from browser)
"""

import sys
import os
import re
import html
import base64
import argparse
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

# Academic Paper Styling for HTML & PDF output
ACADEMIC_CSS = """
@page {
    size: A4;
    margin: 20mm 20mm 20mm 20mm;
    @bottom-right {
        content: counter(page);
        font-family: 'Times New Roman', 'Noto Serif CJK JP', serif;
        font-size: 10pt;
    }
}

body {
    font-family: 'Times New Roman', 'Noto Serif CJK JP', 'Yu Mincho', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #111;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    font-size: 18pt;
    text-align: center;
    margin-top: 24pt;
    margin-bottom: 12pt;
    font-weight: bold;
    border-bottom: 2px solid #333;
    padding-bottom: 8px;
}

h2 {
    font-size: 14pt;
    margin-top: 18pt;
    margin-bottom: 8pt;
    font-weight: bold;
    border-bottom: 1px solid #ddd;
}

h3 {
    font-size: 12pt;
    margin-top: 14pt;
    margin-bottom: 6pt;
    font-weight: bold;
}

blockquote {
    margin: 12pt 0;
    padding: 8pt 16pt;
    background-color: #f8f9fa;
    border-left: 4px solid #0056b3;
    font-style: italic;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 14pt 0;
    font-size: 10pt;
}

th, td {
    border: 1px solid #ccc;
    padding: 6pt 10pt;
    text-align: left;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
}

code {
    font-family: 'Courier New', Courier, monospace;
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 9.5pt;
}

img.mermaid-figure {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 16pt auto;
    border: 1px solid #ddd;
}

pre {
    background-color: #f4f4f4;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
}

.abstract {
    font-size: 10pt;
    margin: 20px 40px;
    padding: 15px;
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}
"""


def ensure_blank_line_before_lists(md_text: str) -> str:
    """Python-Markdown treats 'paragraph\\n- item' as one <p>; insert a blank line."""
    list_item = re.compile(r"^(\s*[-*+]|\s*\d+\.)\s+")
    lines = md_text.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        if i > 0 and list_item.match(line):
            prev = lines[i - 1]
            if prev.strip() and not list_item.match(prev):
                prev_l = prev.lstrip()
                if not prev_l.startswith(("#", "|", ">", "```")):
                    if not out or out[-1].strip() != "":
                        out.append("")
        out.append(line)
    return "\n".join(out) + ("\n" if md_text.endswith("\n") else "")


_MERMAID_FENCE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def _mermaid_cli_command() -> Optional[List[str]]:
    """Return argv prefix for mermaid-cli, or None if unavailable."""
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        return ["npx", "--yes", "@mermaid-js/mermaid-cli"]
    return None


def render_mermaid_fence_to_data_uri(source: str) -> Optional[str]:
    """Render one Mermaid source block to a PNG data URI via mermaid-cli."""
    cli = _mermaid_cli_command()
    if not cli:
        return None
    with tempfile.TemporaryDirectory(prefix="mermaid-") as tmp:
        tmp_path = Path(tmp)
        mmd_path = tmp_path / "diagram.mmd"
        png_path = tmp_path / "diagram.png"
        mmd_path.write_text(source.strip() + "\n", encoding="utf-8")
        cmd = cli + ["-i", str(mmd_path), "-o", str(png_path), "-b", "white"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not png_path.is_file():
            print(
                f"WARN: mermaid-cli failed (rc={res.returncode}): {res.stderr.strip()}",
                file=sys.stderr,
            )
            return None
        b64 = base64.b64encode(png_path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{b64}"


def replace_mermaid_blocks_with_images(md_text: str) -> str:
    """
    Replace ```mermaid fenced blocks with HTML <img> (data URI).

    Keeps Mermaid as the Markdown source of truth; rasterization is a
    conversion-time concern for PDF/HTML deliverables.
    """
    rendered = 0

    def _sub(match: re.Match) -> str:
        nonlocal rendered
        data_uri = render_mermaid_fence_to_data_uri(match.group(1))
        if not data_uri:
            return match.group(0)
        rendered += 1
        return (
            f'\n\n<img class="mermaid-figure" alt="Figure (Mermaid)" '
            f'src="{data_uri}" />\n\n'
        )

    out = _MERMAID_FENCE.sub(_sub, md_text)
    if rendered:
        print(f"INFO: Rendered {rendered} Mermaid diagram(s) to PNG for PDF/HTML.")
    elif _MERMAID_FENCE.search(md_text) and _mermaid_cli_command() is None:
        print(
            "WARN: Mermaid blocks found but mermaid-cli/npx unavailable; "
            "diagrams will appear as code.",
            file=sys.stderr,
        )
    return out


def render_markdown_body(md_text: str) -> str:
    """Render markdown text to clean HTML body content."""
    md_text = ensure_blank_line_before_lists(md_text)
    md_text = replace_mermaid_blocks_with_images(md_text)
    try:
        import markdown
        return markdown.markdown(md_text, extensions=['extra', 'codehilite', 'tables', 'fenced_code', 'toc', 'attr_list'])
    except ImportError:
        pass

    # Basic Fallback Markdown-to-HTML parser if markdown module is missing
    lines = md_text.splitlines()
    html_lines = []
    in_table = False
    in_list = False
    in_code = False
    table_lines = []

    def inline_format(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        return text

    for line in lines:
        sline = line.strip()

        if sline.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            html_lines.append(html.escape(line))
            continue

        if sline.startswith("|"):
            table_lines.append(sline)
            in_table = True
            continue
        elif in_table:
            # Process table
            in_table = False
            if table_lines:
                html_lines.append("<table>")
                header_done = False
                for tline in table_lines:
                    cols = [c.strip() for c in tline.split("|")[1:-1]]
                    if not cols or "---" in cols[0]:
                        header_done = True
                        continue
                    tag = "th" if not header_done else "td"
                    row = "".join([f"<{tag}>{inline_format(c)}</{tag}>" for c in cols])
                    html_lines.append(f"<tr>{row}</tr>")
                html_lines.append("</table>")
                table_lines = []

        if sline.startswith("# "):
            html_lines.append(f"<h1>{inline_format(sline[2:])}</h1>")
        elif sline.startswith("## "):
            html_lines.append(f"<h2>{inline_format(sline[3:])}</h2>")
        elif sline.startswith("### "):
            html_lines.append(f"<h3>{inline_format(sline[4:])}</h3>")
        elif sline.startswith("#### "):
            html_lines.append(f"<h4>{inline_format(sline[5:])}</h4>")
        elif sline.startswith("> "):
            html_lines.append(f"<blockquote>{inline_format(sline[2:])}</blockquote>")
        elif sline.startswith("- ") or sline.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{inline_format(sline[2:])}</li>")
        elif sline.startswith("---") or sline.startswith("***"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
        elif sline:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{inline_format(sline)}</p>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def convert_md_to_pdf(input_md: Path, output_pdf: Path) -> Tuple[bool, str]:
    """
    Attempt conversion using available tools.
    Returns: (is_pdf_generated: bool, output_kind: 'pdf' | 'html' | 'failed')
    """
    input_md = input_md.resolve()
    output_pdf = output_pdf.resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Method 1: Pandoc
    if shutil.which("pandoc"):
        print("INFO: Using pandoc for PDF conversion...")
        cmd = ["pandoc", str(input_md), "-o", str(output_pdf), "--pdf-engine=xelatex"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and output_pdf.exists():
            print(f"SUCCESS: Generated PDF at {output_pdf}")
            return True, "pdf"
        # Try pandoc without xelatex engine specified
        cmd2 = ["pandoc", str(input_md), "-o", str(output_pdf)]
        res2 = subprocess.run(cmd2, capture_output=True, text=True)
        if res2.returncode == 0 and output_pdf.exists():
            print(f"SUCCESS: Generated PDF via pandoc at {output_pdf}")
            return True, "pdf"

    # Prepare rendered HTML body for WeasyPrint and Headless Browsers
    md_text = input_md.read_text(encoding="utf-8")
    body_html = render_markdown_body(md_text)
    html_file = output_pdf.with_suffix(".html")
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{html.escape(input_md.stem)}</title>
<style>
{ACADEMIC_CSS}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""
    html_file.write_text(html_content, encoding="utf-8")

    # Method 2: WeasyPrint
    if shutil.which("weasyprint"):
        print("INFO: Using WeasyPrint for PDF conversion...")
        cmd = ["weasyprint", str(html_file), str(output_pdf)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and output_pdf.exists():
            print(f"SUCCESS: Generated PDF via WeasyPrint at {output_pdf}")
            return True, "pdf"

    # Method 3: HTML Export + Headless Browser
    for browser_cmd in ["google-chrome", "chrome", "chromium", "microsoft-edge"]:
        if shutil.which(browser_cmd):
            print(f"INFO: Using {browser_cmd} headless to render PDF...")
            cmd = [
                browser_cmd,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={output_pdf}",
                str(html_file)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and output_pdf.exists():
                print(f"SUCCESS: Generated PDF via {browser_cmd} at {output_pdf}")
                return True, "pdf"

    print(f"NOTE: Created HTML version ({html_file}). To generate PDF, open this HTML file in your browser and print to PDF.")
    return False, "html"


def main():
    parser = argparse.ArgumentParser(description="Convert Academic Markdown paper to PDF/HTML.")
    parser.add_argument("input_md", type=Path, help="Path to input Markdown file")
    parser.add_argument("-o", "--output", type=Path, help="Path to output PDF file (optional)")

    args = parser.parse_args()

    if not args.input_md.exists():
        print(f"Error: Input file {args.input_md} does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_pdf = args.output
    else:
        # Auto-detect manuscript/ output directory if available
        parent_dir = args.input_md.parent
        manuscript_dir = parent_dir / "manuscript" if parent_dir.name != "manuscript" else parent_dir
        if not manuscript_dir.exists() and (parent_dir.parent / "manuscript").exists():
            manuscript_dir = parent_dir.parent / "manuscript"
        
        if manuscript_dir.exists():
            out_pdf = manuscript_dir / args.input_md.with_suffix(".pdf").name
        else:
            out_pdf = args.input_md.with_suffix(".pdf")

    is_pdf, kind = convert_md_to_pdf(args.input_md, out_pdf)
    if not is_pdf:
        print(f"Warning: PDF conversion failed or fallback to HTML ({kind}).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
