#!/usr/bin/env python3
"""
PDF Paper to Markdown Converter with Embedded Image Extraction.
Uses ONLY Python standard library (zlib, re, struct, pathlib, argparse, sys).
Extracts text streams and embedded images (JPEG/PPM) without external dependencies.

Known Limitations:
  - Encrypted/password-protected PDFs are detected and rejected with a clear error.
  - CIDFont-based CJK (Japanese/Chinese/Korean) PDFs may yield empty or garbled text
    because this parser decodes text streams as latin1. For reliable CJK PDF extraction,
    consider using an external library such as pymupdf (fitz) or pdfplumber.
  - PDFs without embedded text (scanned image-only PDFs) will produce an empty text body.
"""

import sys
import os
import re
import zlib
import argparse
from pathlib import Path


def unescape_pdf_string(s: str) -> str:
    """Unescape special characters in PDF string (e.g. \\( \\) \\\\ \\n \\r)."""
    s = s.replace(r'\(', '(').replace(r'\)', ')').replace(r'\\', '\\')
    s = s.replace(r'\n', '\n').replace(r'\r', '\r').replace(r'\t', '\t')
    return s


def parse_pdf_text_operators(stream_bytes: bytes) -> str:
    """Extract plain text from decompressed PDF content stream bytes."""
    text_chunks = []
    
    # Try decoding stream
    try:
        content = stream_bytes.decode('latin1')
    except Exception:
        return ""
        
    # Match BT ... ET blocks
    bt_blocks = re.findall(r'BT\s*(.*?)\s*ET', content, flags=re.DOTALL)
    for block in bt_blocks:
        # Match (text) Tj
        tj_matches = re.findall(r'\((.*?)\)\s*Tj', block, flags=re.DOTALL)
        for m in tj_matches:
            text_chunks.append(unescape_pdf_string(m))
            
        # Match [(text1) -10 (text2)] TJ
        tj_array_matches = re.findall(r'\[(.*?)\]\s*TJ', block, flags=re.DOTALL)
        for array_content in tj_array_matches:
            array_texts = re.findall(r'\((.*?)\)', array_content, flags=re.DOTALL)
            text_chunks.append("".join([unescape_pdf_string(t) for t in array_texts]))
            
        # Match <HexText> Tj
        hex_matches = re.findall(r'<(.*?)>\s*Tj', block, flags=re.DOTALL)
        for h in hex_matches:
            try:
                cleaned_h = re.sub(r'\s+', '', h)
                text_chunks.append(bytes.fromhex(cleaned_h).decode('utf-8', errors='ignore'))
            except Exception:
                pass
                
    return " ".join(text_chunks)


def extract_images_from_pdf_stream(pdf_bytes: bytes, output_assets_dir: Path) -> list[str]:
    """
    Extract embedded images from raw PDF byte content using Python standard library.
    Saves JPEGs (/DCTDecode) directly and FlateDecode images as PPM.
    Returns list of relative image filenames.
    """
    saved_images = []
    output_assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Search for image objects in PDF
    # Pattern: obj ... /Subtype /Image ... stream ... endstream
    obj_blocks = re.findall(rb'(\d+\s+\d+\s+obj.*?endobj)', pdf_bytes, flags=re.DOTALL)
    
    img_counter = 1
    for obj_data in obj_blocks:
        if b'/Subtype' in obj_data and b'/Image' in obj_data:
            stream_match = re.search(rb'stream\r?\n(.*?)\r?\nendstream', obj_data, flags=re.DOTALL)
            if not stream_match:
                continue
                
            stream_bytes = stream_match.group(1)
            
            # Check filter type
            if b'/DCTDecode' in obj_data or b'/DCT' in obj_data:
                # Lossless raw JPEG stream
                img_name = f"extracted_image_{img_counter}.jpg"
                img_path = output_assets_dir / img_name
                img_path.write_bytes(stream_bytes)
                saved_images.append(img_name)
                img_counter += 1
                
            elif b'/FlateDecode' in obj_data:
                # Decompress FlateDecode raw pixels
                try:
                    decompressed = zlib.decompress(stream_bytes)
                    width_m = re.search(rb'/Width\s+(\d+)', obj_data)
                    height_m = re.search(rb'/Height\s+(\d+)', obj_data)
                    
                    if width_m and height_m:
                        width = int(width_m.group(1))
                        height = int(height_m.group(1))
                        
                        # Check ColorSpace
                        bpp = 3 if b'/DeviceRGB' in obj_data else 1
                        expected_len = width * height * bpp
                        
                        if len(decompressed) >= expected_len:
                            img_name = f"extracted_image_{img_counter}.ppm"
                            img_path = output_assets_dir / img_name
                            
                            # Write PPM P6 (RGB) or P5 (Grayscale) header
                            ppm_header = f"P{'6' if bpp == 3 else '5'}\n{width} {height}\n255\n".encode('ascii')
                            img_path.write_bytes(ppm_header + decompressed[:expected_len])
                            saved_images.append(img_name)
                            img_counter += 1
                except zlib.error as e:
                    print(f"Warning: Could not decompress image object: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"Warning: Unexpected error extracting image: {e}", file=sys.stderr)
                    
    return saved_images


def convert_pdf_to_markdown(pdf_path: Path, output_dir: Path = None) -> tuple[Path, list[str]]:
    """
    Convert PDF to Markdown with embedded image extraction.
    Returns (output_md_path, list_of_extracted_images).
    
    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the PDF is encrypted/password-protected.
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
        
    if output_dir is None:
        output_dir = pdf_path.parent
    else:
        output_dir = Path(output_dir).resolve()
        
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    
    pdf_bytes = pdf_path.read_bytes()
    
    # 0. Detect encrypted PDFs
    if b'/Encrypt' in pdf_bytes:
        raise ValueError(
            f"PDF file '{pdf_path.name}' is encrypted/password-protected. "
            "This tool cannot process encrypted PDFs. Please decrypt the file first "
            "or use an external library such as pymupdf."
        )
    
    # 1. Extract Images
    extracted_images = extract_images_from_pdf_stream(pdf_bytes, assets_dir)
    
    # 2. Extract Text Streams
    extracted_text_blocks = []
    
    # Try pdftotext (poppler-utils) first for high-quality text extraction
    try:
        import subprocess
        res = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            raw_text = res.stdout.strip()
            # Split into double-newline paragraphs
            blocks = [b.strip() for b in raw_text.split('\n\n') if b.strip()]
            if blocks:
                extracted_text_blocks = blocks
    except Exception as e:
        print(f"Note: pdftotext fallback not used: {e}", file=sys.stderr)

    # Fallback to pure Python stream parsing if pdftotext wasn't available or yielded nothing
    if not extracted_text_blocks:
        streams = re.findall(rb'stream\r?\n(.*?)\r?\nendstream', pdf_bytes, flags=re.DOTALL)
        for s_bytes in streams:
            # Try uncompressing if FlateDecode
            text = ""
            try:
                decompressed = zlib.decompress(s_bytes)
                text = parse_pdf_text_operators(decompressed)
            except zlib.error:
                # Not a FlateDecode stream or corrupted; try raw parsing
                text = parse_pdf_text_operators(s_bytes)
            except Exception as e:
                print(f"Warning: Error processing stream: {e}", file=sys.stderr)
                text = parse_pdf_text_operators(s_bytes)
                
            if text.strip():
                extracted_text_blocks.append(text.strip())
            
    # 3. Format into Markdown
    doc_title = pdf_path.stem.replace('_', ' ').replace('-', ' ').title()
    md_lines = [f"# {doc_title}\n"]
    
    if extracted_text_blocks:
        for idx, block in enumerate(extracted_text_blocks, 1):
            # Format heuristics for headings and paragraphs
            lines = block.split('. ')
            first_line = lines[0] if lines else block
            
            if len(first_line) < 60 and not first_line.endswith('.'):
                md_lines.append(f"## {first_line}\n")
                if len(lines) > 1:
                    md_lines.append(". ".join(lines[1:]) + "\n")
            else:
                md_lines.append(block + "\n")
    else:
        md_lines.append("*Note: No plain text streams could be decoded directly. Content may be scanned or image-based.*\n")
        
    # 4. Embed Images in Markdown
    if extracted_images:
        md_lines.append("## 🖼️ Extracted Figures & Images\n")
        for img_name in extracted_images:
            md_lines.append(f"![{img_name}](assets/{img_name})\n")
            
    output_md_path = output_dir / f"{pdf_path.stem}.md"
    output_md_path.write_text("\n".join(md_lines), encoding='utf-8')
    
    return output_md_path, extracted_images


def main():
    parser = argparse.ArgumentParser(description="Convert PDF paper to Markdown with embedded image extraction (Standard Library Only).")
    parser.add_argument("pdf_file", help="Path to input PDF paper file")
    parser.add_argument("--output-dir", "-o", help="Output directory path (defaults to same directory as PDF)")
    
    args = parser.parse_args()
    pdf_path = Path(args.pdf_file)
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    try:
        md_path, images = convert_pdf_to_markdown(pdf_path, output_dir=output_dir)
        print(f"✅ Successfully converted PDF to Markdown:")
        print(f"   📄 Markdown File: {md_path}")
        print(f"   🖼️ Extracted Images: {len(images)} image(s) saved in {md_path.parent / 'assets'}")
    except Exception as e:
        print(f"❌ Error converting PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
