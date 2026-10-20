"""
Markdown <-> Notion Block converter.
Handles bi-directional conversion between Markdown and Notion block JSON structure,
including native Tables, Callout Cards, Rich-Text (bold, code, links, italic),
and structured lists.
"""
import re
from typing import List, Dict, Any, Tuple

NOTION_TEXT_LIMIT = 2000

INLINE_PATTERN = re.compile(
    r'(?P<link>\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^\)]+)\))|'
    r'(?P<bold_code>\*\*`(?P<bc_text>[^`]+)`\*\*)|'
    r'(?P<code>`(?P<code_text>[^`]+)`)|'
    r'(?P<bold>\*\*(?P<bold_text>.+?)\*\*)|'
    r'(?P<italic>\*(?P<italic_text>.+?)\*)|'
    r'(?P<strike>~~(?P<strike_text>.+?)~~)'
)

def _chunk_text(text: str, limit: int = NOTION_TEXT_LIMIT) -> List[str]:
    """Split text into chunks that satisfy Notion's character limit."""
    if not text:
        return [""]
    return [text[i:i + limit] for i in range(0, len(text), limit)]

def _create_rich_text(text: str) -> List[Dict[str, Any]]:
    """Legacy helper for plain rich text."""
    return _parse_rich_text(text)

def _parse_rich_text(text: str) -> List[Dict[str, Any]]:
    """Parse inline markdown (bold, italic, code, links) into Notion rich text array."""
    if not text:
        return []

    rich_texts: List[Dict[str, Any]] = []
    last_idx = 0

    for match in INLINE_PATTERN.finditer(text):
        start, end = match.span()
        if start > last_idx:
            chunk = text[last_idx:start]
            for c in _chunk_text(chunk):
                rich_texts.append({
                    "type": "text",
                    "text": {"content": c}
                })

        if match.group("link"):
            lt = match.group("link_text")
            lu = match.group("link_url")
            for c in _chunk_text(lt):
                rich_texts.append({
                    "type": "text",
                    "text": {"content": c, "link": {"url": lu}}
                })
        elif match.group("bold_code"):
            bct = match.group("bc_text")
            for c in _chunk_text(bct):
                rich_texts.append({
                    "type": "text",
                    "text": {"content": c},
                    "annotations": {"bold": True, "code": True}
                })
        elif match.group("code"):
            ct = match.group("code_text")
            for c in _chunk_text(ct):
                rich_texts.append({
                    "type": "text",
                    "text": {"content": c},
                    "annotations": {"code": True}
                })
        elif match.group("bold"):
            bt = match.group("bold_text")
            # If bold contains inline code like `foo`
            if bt.startswith("`") and bt.endswith("`") and len(bt) > 2:
                for c in _chunk_text(bt[1:-1]):
                    rich_texts.append({
                        "type": "text",
                        "text": {"content": c},
                        "annotations": {"bold": True, "code": True}
                    })
            else:
                for c in _chunk_text(bt):
                    rich_texts.append({
                        "type": "text",
                        "text": {"content": c},
                        "annotations": {"bold": True}
                    })
        elif match.group("italic"):
            it = match.group("italic_text")
            for c in _chunk_text(it):
                rich_texts.append({
                    "type": "text",
                    "text": {"content": c},
                    "annotations": {"italic": True}
                })
        elif match.group("strike"):
            st = match.group("strike_text")
            for c in _chunk_text(st):
                rich_texts.append({
                    "type": "text",
                    "text": {"content": c},
                    "annotations": {"strikethrough": True}
                })

        last_idx = end

    if last_idx < len(text):
        chunk = text[last_idx:]
        for c in _chunk_text(chunk):
            rich_texts.append({
                "type": "text",
                "text": {"content": c}
            })

    return rich_texts if rich_texts else [{"type": "text", "text": {"content": ""}}]

def _extract_callout_icon_and_text(raw_content: str) -> Tuple[str, str, str]:
    """Detect emoji or GitHub alert tag and background color to format as a rich Callout card."""
    content = raw_content.strip()
    if not content:
        return "💡", "", "gray_background"

    # 1. Explicit background tag detection, e.g. {bg:blue} or [color:blue_background]
    color = None
    bg_match = re.match(r'^\{bg:([a-z_]+)\}\s*', content) or re.match(r'^\[color:([a-z_]+)\]\s*', content)
    if bg_match:
        raw_c = bg_match.group(1).lower()
        if not raw_c.endswith("_background") and raw_c in ("gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink", "red"):
            color = f"{raw_c}_background"
        elif raw_c in ("gray_background", "brown_background", "orange_background", "yellow_background", "green_background", "blue_background", "purple_background", "pink_background", "red_background", "default"):
            color = raw_c
        content = content[bg_match.end():].strip()

    alert_map = {
        "[!NOTE]": ("ℹ️", "blue_background"),
        "[!TIP]": ("💡", "purple_background"),
        "[!IMPORTANT]": ("❗", "yellow_background"),
        "[!WARNING]": ("⚠️", "red_background"),
        "[!CAUTION]": ("🛑", "red_background")
    }
    for tag, (em, c_bg) in alert_map.items():
        if content.startswith(tag):
            return em, content[len(tag):].strip(), (color or c_bg)

    def _is_emoji(ch: str) -> bool:
        if not ch: return False
        cp = ord(ch[0])
        return (
            (0x1F300 <= cp <= 0x1FAFF) or
            (0x2600 <= cp <= 0x27BF) or
            (0x2300 <= cp <= 0x23FF) or
            cp in (0x2B50, 0x2B55, 0x2934, 0x2935, 0x3030, 0x303D, 0x3297, 0x3299)
        )

    # Heuristic emoji to color mapping
    emoji_colors = {
        "📈": "blue_background",
        "⏱️": "blue_background",
        "📊": "blue_background",
        "🕒": "green_background",
        "🗓️": "green_background",
        "📅": "green_background",
        "🏆": "green_background",
        "✅": "green_background",
        "🌿": "green_background",
        "🎯": "purple_background",
        "💡": "purple_background",
        "🔮": "purple_background",
        "⚡": "yellow_background",
        "⭐": "yellow_background",
        "🟡": "yellow_background",
        "🚨": "red_background",
        "⚠️": "red_background",
        "🛑": "red_background",
        "📦": "brown_background",
        "📁": "brown_background",
        "🗄️": "brown_background",
        "👤": "orange_background",
        "👥": "orange_background",
        "🏢": "orange_background"
    }

    detected_emoji = "🎯"
    parsed_text = content

    # Check if first character is an emoji
    if len(content) > 1 and content[1] == '\ufe0f' and _is_emoji(content[0]):
        detected_emoji = content[:2]
        parsed_text = content[2:].strip()
    elif len(content) > 0 and _is_emoji(content[0]):
        detected_emoji = content[0]
        parsed_text = content[1:].strip()

    final_color = color or emoji_colors.get(detected_emoji, "gray_background")
    return detected_emoji, parsed_text, final_color

def markdown_to_blocks(md_content: str) -> List[Dict[str, Any]]:
    """
    Parse a markdown string into a list of Notion block objects.
    Supports native Tables, Callouts, Headings, Lists, To-Dos, Code blocks, Dividers, and Paragraphs.
    """
    blocks: List[Dict[str, Any]] = []
    lines = md_content.splitlines()
    in_code_block = False
    code_lang = "plain text"
    code_lines: List[str] = []

    valid_languages = {
        "abap", "abc", "agda", "arduino", "ascii art", "assembly", "bash", "basic", "bnf",
        "c", "c#", "c++", "clojure", "coffeescript", "coq", "css", "dart", "dhall", "diff",
        "docker", "ebnf", "elixir", "elm", "erlang", "f#", "flow", "fortran", "gherkin",
        "glsl", "go", "graphql", "groovy", "haskell", "hcl", "html", "idris", "java",
        "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", "livescript",
        "llvm ir", "lua", "makefile", "markdown", "markup", "matlab", "mathematica",
        "mermaid", "nix", "notion formula", "objective-c", "ocaml", "pascal", "perl", "php",
        "plain text", "powershell", "prolog", "protobuf", "purescript", "python", "r",
        "racket", "reason", "ruby", "rust", "sass", "scala", "scheme", "scss", "shell",
        "smalltalk", "solidity", "sql", "swift", "toml", "typescript", "vb.net", "verilog",
        "vhdl", "visual basic", "webassembly", "xml", "yaml", "java/c/c++/c#"
    }
    lang_aliases = {
        "text": "plain text",
        "txt": "plain text",
        "sh": "shell",
        "zsh": "shell",
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "yml": "yaml",
        "dockerfile": "docker"
    }

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Handle code blocks
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                raw_lang = stripped[3:].strip().lower()
                code_lang = lang_aliases.get(raw_lang, raw_lang)
                if code_lang not in valid_languages:
                    code_lang = "plain text"
                code_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": _chunk_text_to_plain(code_text),
                        "language": code_lang
                    }
                })
                code_lines = []
                i += 1
                continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Divider
        if stripped in ("---", "***", "___"):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
            continue

        # Markdown Table Detection
        if stripped.startswith("|") and stripped.endswith("|") and i + 1 < n:
            next_line = lines[i + 1].strip()
            if next_line.startswith("|") and ("---" in next_line or ":---" in next_line):
                # Header row
                header_cells = [c.strip() for c in stripped.strip("|").split("|")]
                i += 2  # Skip header and delimiter

                # Collect all data rows
                data_rows: List[List[str]] = []
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    row_cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    data_rows.append(row_cells)
                    i += 1

                # Calculate columns count
                col_count = len(header_cells)
                for dr in data_rows:
                    if len(dr) > col_count:
                        col_count = len(dr)

                # Format rows
                table_children: List[Dict[str, Any]] = []
                all_rows = [header_cells] + data_rows
                for row in all_rows:
                    padded_row = row + [""] * (col_count - len(row))
                    cell_rich_texts = [_parse_rich_text(c) for c in padded_row[:col_count]]
                    table_children.append({
                        "type": "table_row",
                        "table_row": {"cells": cell_rich_texts}
                    })

                blocks.append({
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": col_count,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": table_children
                    }
                })
                continue

        # Headings
        if stripped.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": _parse_rich_text(stripped[4:])}
            })
            i += 1
            continue
        elif stripped.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": _parse_rich_text(stripped[3:])}
            })
            i += 1
            continue
        elif stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": _parse_rich_text(stripped[2:])}
            })
            i += 1
            continue

        # Checklists / To-Dos
        if stripped.startswith("- [ ] ") or stripped.startswith("* [ ] "):
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": _parse_rich_text(stripped[6:]),
                    "checked": False
                }
            })
            i += 1
            continue
        elif stripped.startswith("- [x] ") or stripped.startswith("- [X] ") or stripped.startswith("* [x] "):
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": _parse_rich_text(stripped[6:]),
                    "checked": True
                }
            })
            i += 1
            continue

        # Bulleted list
        if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("+ "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _parse_rich_text(stripped[2:])}
            })
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s", stripped):
            content = re.sub(r"^\d+\.\s", "", stripped)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": _parse_rich_text(content)}
            })
            i += 1
            continue

        # Callouts & Blockquotes
        if stripped.startswith("> "):
            raw_quote = stripped[2:].strip()
            emoji, text, color = _extract_callout_icon_and_text(raw_quote)
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": _parse_rich_text(text),
                    "icon": {"type": "emoji", "emoji": emoji},
                    "color": color
                }
            })
            i += 1
            continue

        # Video Embed (e.g. YouTube lo-fi focus streams)
        if stripped.startswith("https://www.youtube.com/") or stripped.startswith("https://youtu.be/"):
            blocks.append({
                "object": "block",
                "type": "video",
                "video": {
                    "type": "external",
                    "external": {"url": stripped}
                }
            })
            i += 1
            continue

        # Paragraph
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": _parse_rich_text(line)}
        })
        i += 1

    # If code block wasn't closed
    if in_code_block and code_lines:
        blocks.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": _chunk_text_to_plain("\n".join(code_lines)),
                "language": code_lang
            }
        })

    return blocks

def _chunk_text_to_plain(text: str) -> List[Dict[str, Any]]:
    chunks = _chunk_text(text)
    return [{"type": "text", "text": {"content": c}} for c in chunks]

def _extract_rich_text(rich_texts: List[Dict[str, Any]]) -> str:
    """Extract plain text from Notion rich text array."""
    if not rich_texts:
        return ""
    return "".join(t.get("plain_text", "") for t in rich_texts)

def blocks_to_markdown(blocks: List[Dict[str, Any]]) -> str:
    """
    Convert a list of Notion block objects into Markdown string.
    """
    md_lines = []
    numbered_counter = 1

    for block in blocks:
        btype = block.get("type", "")
        data = block.get(btype, {})

        if btype == "heading_1":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"# {text}\n")
            numbered_counter = 1
        elif btype == "heading_2":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"## {text}\n")
            numbered_counter = 1
        elif btype == "heading_3":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"### {text}\n")
            numbered_counter = 1
        elif btype == "bulleted_list_item":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"- {text}")
            numbered_counter = 1
        elif btype == "numbered_list_item":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"{numbered_counter}. {text}")
            numbered_counter += 1
        elif btype == "to_do":
            text = _extract_rich_text(data.get("rich_text", []))
            mark = "x" if data.get("checked", False) else " "
            md_lines.append(f"- [{mark}] {text}")
            numbered_counter = 1
        elif btype == "quote":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"> {text}\n")
            numbered_counter = 1
        elif btype == "callout":
            text = _extract_rich_text(data.get("rich_text", []))
            icon = data.get("icon", {}).get("emoji", "💡")
            md_lines.append(f"> {icon} {text}\n")
            numbered_counter = 1
        elif btype == "table":
            # Extract table rows
            table_children = block.get("children", [])
            for idx, tr in enumerate(table_children):
                cells = tr.get("table_row", {}).get("cells", [])
                cell_strs = [_extract_rich_text(c) for c in cells]
                md_lines.append("| " + " | ".join(cell_strs) + " |")
                if idx == 0 and len(cell_strs) > 0:
                    md_lines.append("| " + " | ".join([":---"] * len(cell_strs)) + " |")
            numbered_counter = 1
        elif btype == "code":
            text = _extract_rich_text(data.get("rich_text", []))
            lang = data.get("language", "")
            md_lines.append(f"```{lang}\n{text}\n```\n")
            numbered_counter = 1
        elif btype == "divider":
            md_lines.append("---\n")
            numbered_counter = 1
        elif btype == "paragraph":
            text = _extract_rich_text(data.get("rich_text", []))
            md_lines.append(f"{text}\n")
            numbered_counter = 1
        else:
            text = _extract_rich_text(data.get("rich_text", []))
            if text:
                md_lines.append(f"{text}\n")
            numbered_counter = 1

    return "\n".join(md_lines).strip()
