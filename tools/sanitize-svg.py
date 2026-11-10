#!/usr/bin/env python3
"""Repair the SVG files GitAscii renders so browsers can load them.

Two generator defects currently break the SVG as an <img>:
  * duplicate attributes on one element  -> "duplicate attribute" XML error
  * stray closing tags                  -> mismatched-tag XML error

Both are fatal for image decoding, so GitHub shows the alt text instead.

Usage: sanitize-svg.py <in.svg> [<out.svg>]   (out defaults to in-place)
"""

import re
import sys

ATTR = re.compile(r"""([A-Za-z_:][-\w.:]*)\s*=\s*("[^"]*"|'[^']*')""")
NAME = re.compile(r"<\s*(/?)\s*([A-Za-z_][-\w.:]*)")


def _scan_tag(src: str, start: int) -> tuple[int, int]:
    """Return (start, end) of the tag starting at `start`, honouring quotes."""
    i = start + 1
    quote = None
    n = len(src)
    while i < n:
        ch = src[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            return start, i + 1
        i += 1
    return start, n


def _dedupe_attrs(tag: str) -> str:
    seen: set[str] = set()
    result = []
    last = 0
    for m in ATTR.finditer(tag):
        name = m.group(1)
        if name in seen:
            result.append(tag[last:m.start()])
            last = m.end()
            continue
        seen.add(name)
    result.append(tag[last:])
    return "".join(result)


def dedupe_duplicate_attributes(src: str) -> str:
    out = []
    i = 0
    n = len(src)
    while i < n:
        if src[i] != "<":
            j = src.find("<", i)
            if j == -1:
                j = n
            out.append(src[i:j])
            i = j
            continue
        start, end = _scan_tag(src, i)
        out.append(_dedupe_attrs(src[start:end]))
        i = end
    return "".join(out)


def drop_stray_closers(src: str) -> tuple[str, int]:
    out = []
    stack: list[str] = []
    dropped = 0
    i = 0
    n = len(src)
    while i < n:
        if src[i] != "<":
            j = src.find("<", i)
            if j == -1:
                j = n
            out.append(src[i:j])
            i = j
            continue
        start, end = _scan_tag(src, i)
        tag = src[start:end]
        m = NAME.match(tag)
        if m:
            closing, name = m.group(1), m.group(2)
            self_closing = tag.rstrip().endswith("/>")
            if closing:
                if stack and stack[-1] == name:
                    stack.pop()
                    out.append(tag)
                else:
                    dropped += 1  # no matching opener: skip it
            else:
                if not self_closing:
                    stack.append(name)
                out.append(tag)
        else:
            out.append(tag)
        i = end
    return "".join(out), dropped


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else path
    src = open(path, encoding="utf-8").read()

    fixed = dedupe_duplicate_attributes(src)
    fixed, dropped = drop_stray_closers(fixed)

    import xml.etree.ElementTree as ET

    try:
        ET.fromstring(fixed)
    except Exception as exc:  # still not loadable
        print(f"ERROR: {path} still invalid after sanitize: {exc}", file=sys.stderr)
        sys.exit(2)

    open(out, "w", encoding="utf-8").write(fixed)
    print(f"sanitized {path} -> {out} (stray tags dropped: {dropped}, bytes: {len(fixed)})")


if __name__ == "__main__":
    main()
