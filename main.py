"""
Retro terminal GIF for the GitHub profile README.

Renders a boot sequence -> login -> `fetch.sh` (neofetch) into output.gif using
x0rzavi/github-readme-terminal (`gifos`): https://github.com/x0rzavi/github-readme-terminal

Setup
-----
    python -m pip install --upgrade github-readme-terminal
    # FFmpeg must be on PATH
    # Optional colour scheme (otherwise ~/.config/gifos/gifos_settings.toml is used)
    export GIFOS_GENERAL_USER_NAME="roshan@if1eight0sty"
    export GIFOS_GENERAL_COLOR_SCHEME="yoru"

Run
---
    python main.py            # writes output.gif + updates README snippet

Fonts
-----
The GitHub avatar is fetched at render time (github.com/<user>.png), so the GIF
always matches the current profile picture; ASCII art is the offline fallback.

`gohufont-uni-14` ships with the package. Drop extra fonts in ./fonts and point
DISPLAY_FONT / ART_FONT at them (see below). Anything you add must be licensed
for redistribution if you commit it.
"""

import urllib.request
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import gifos
from gifos.gifos import font_path as _gifos_font_path
from PIL import Image, ImageOps

# --- fonts -----------------------------------------------------------------
# Bitmap body font: bundled with gifos, so no file to ship.
_BUNDLED_FONT = _gifos_font_path / "gohufont-uni-14.pil"
FONT_BODY = str(_BUNDLED_FONT) if _BUNDLED_FONT.exists() else ""
# Chunky display font for the splash wordmark (optional, e.g. vtks-blocketo).
DISPLAY_FONT = "./fonts/vtks-blocketo.regular.ttf"
# Font used for the ASCII-art panel (optional).
ART_FONT = "./fonts/Inversionz.otf"

TZ = ZoneInfo("Asia/Kathmandu")

# --- palette (matches roshanaryanmajhi.com.np) ------------------------------
# #98cbff primary -> 94, #61dac1 secondary -> 96, #ffb77d tertiary -> 93
C_PRIMARY = "\x1b[94m"
C_SECONDARY = "\x1b[96m"
C_TERTIARY = "\x1b[93m"
C_DIM = "\x1b[90m"
C_RESET = "\x1b[0m"
C_BADGE = "\x1b[30;104m"  # black on blue

HANDLE = "if1eight0sty"
HOST = "roshan@if1eight0sty"

# GitHub avatar, pulled at render time so the GIF always tracks the profile picture.
AVATAR_URL = f"https://github.com/{HANDLE}.png?size=460"
AVATAR_PATH = Path("./temp/avatar.png")
AVATAR_SIZE = 0.5  # multiplier passed to paste_image()

# The "logo" from the README neofetch block, dropped into the terminal.
NEOFETCH_ART = r"""
       .__    :    __.       {host}
      /   \   :   /   \      --------------------------
     .____ \ _v_ / ____.     OS:       if1eight0sty 24.04 LTS
    /     \ /^^^\ /     \    Role:     Software Engineer @ Pexus Tech
    \      \\^^^//      /    Org:      ING Consulting (Innovate Nepal Group)
      .-----X{{"}}X-----.      Editor:   IFIEIGHT0STY_IDE
     /     /(o o)\     \     Stack:    React · TS · Node · PG
    /     /  (")  \     \    Location: Kathmandu, Nepal (UTC+5:45)
    \     \       /     /    Also:     External Project Supervisor
           \     /           Status:   open to software engineer roles
            ---
""".format(host=HOST)


def boot_sequence(t: "gifos.Terminal") -> None:
    """Fake BIOS POST, in the spirit of the original project."""
    t.gen_text("", 1, count=20)
    t.toggle_show_cursor(False)
    year = datetime.now(TZ).strftime("%Y")

    t.gen_text("IF1EIGHT0STY Modular BIOS v2.0.24", 1)
    t.gen_text(f"Copyright (C) {year}, {C_TERTIARY}Roshan Aryan Majhi{C_RESET}", 2)
    t.gen_text(f"{C_PRIMARY}GitHub Profile ReadMe Terminal, Rev 1011{C_RESET}", 4)
    t.gen_text("Monolith(tm) IFCPU - 250Hz", 6)
    t.gen_text(
        f"Press {C_PRIMARY}DEL{C_RESET} to enter SETUP, {C_PRIMARY}ESC{C_RESET} to cancel Memory Test",
        t.num_rows,
    )

    for i in range(0, 65653, 16384):  # 64K memory test (coarse: keeps the GIF short)
        t.delete_row(7)
        # slow down early on so the numbers are readable, then let it rip
        t.gen_text(f"Memory Test: {i}", 7, count=1, contin=True)
    t.delete_row(7)
    t.gen_text("Memory Test: 64KB OK", 7, count=10, contin=True)
    t.gen_text("", 11, count=10, contin=True)


def splash(t: "gifos.Terminal") -> None:
    """Optional block-letter splash. Falls back silently if the font is absent."""
    import os

    t.clear_frame()
    t.gen_text("Initiating Boot Sequence ", 1, contin=True)
    t.gen_typing_text(".....", 1, contin=True)

    if not os.path.exists(DISPLAY_FONT):
        t.gen_text(f"{C_SECONDARY}IF1EIGHT0STY{C_RESET}", 8, contin=True)
        return

    t.set_font(DISPLAY_FONT, 66)
    word = "IF1EIGHT0STY"
    mid_row = (t.num_rows + 1) // 2
    mid_col = max(1, (t.num_cols - len(word) + 1) // 2)
    for line in gifos.effects.text_scramble_effect_lines(word, 3, include_special=False):
        t.delete_row(mid_row + 1)
        t.gen_text(line, mid_row + 1, mid_col)
    t.set_font(FONT_BODY)


def login(t: "gifos.Terminal") -> None:
    t.clear_frame()
    t.clone_frame(5)
    t.toggle_show_cursor(False)
    t.gen_text(f"{C_TERTIARY}IF1EIGHT0STY OS v2.0.24 (tty1){C_RESET}", 1, count=5)

    t.gen_text("login: ", 3, count=5)
    t.toggle_show_cursor(True)
    t.gen_typing_text("roshan", 3, contin=True)

    t.gen_text("", 4, count=5)
    t.toggle_show_cursor(False)
    t.gen_text("password: ", 4, count=5)
    t.toggle_show_cursor(True)
    t.gen_typing_text("*********", 4, contin=True)

    t.toggle_show_cursor(False)
    now = datetime.now(TZ).strftime("%a %b %d %I:%M:%S %p %Z %Y")
    t.gen_text(f"Last login: {now} on tty1", 6)


def fetch_avatar() -> Path | None:
    """Download the GitHub avatar so the terminal shows the current profile picture."""
    try:
        AVATAR_PATH.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            AVATAR_URL, headers={"User-Agent": f"{HANDLE}-profile-gif"}
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            AVATAR_PATH.write_bytes(response.read())
        print(f"INFO: avatar downloaded -> {AVATAR_PATH}")
        return AVATAR_PATH
    except Exception as exc:  # offline, rate limit, network hiccup
        print(f"WARNING: could not fetch avatar ({exc}); falling back to ASCII art")
        return None


def paste_avatar(t: "gifos.Terminal", path: Path) -> bool:
    """Paste the avatar bitmap. gifos exposes paste_image(); older builds pasteImage()."""
    fn = getattr(t, "paste_image", None) or getattr(t, "pasteImage", None)
    if fn is None:
        print("WARNING: gifos build has no image paste API")
        return False
    try:
        fn(str(path), 2, 1, AVATAR_SIZE)
        return True
    except TypeError:
        try:  # legacy camelCase signature
            fn(str(path), row_num=2, col_num=1, sizeMulti=AVATAR_SIZE)
            return True
        except Exception as exc:
            print(f"WARNING: legacy paste API failed ({exc})")
            return False
    except Exception as exc:
        print(f"WARNING: paste failed ({exc})")
        return False


def fetch(t: "gifos.Terminal") -> None:
    """neofetch: GitHub avatar on the left, profile facts on the right."""
    t.clear_frame()
    t.gen_prompt(1)
    prompt_col = t.curr_col
    t.clone_frame(10)
    t.toggle_show_cursor(True)
    t.gen_typing_text("fetch.s", 1, contin=True)
    t.delete_row(1, prompt_col)
    t.gen_text(f"\x1b[92mfetch.sh{C_RESET}", 1, contin=True)
    t.gen_typing_text(f" -u {HANDLE}", 1, contin=True)

    t.toggle_show_cursor(False)
    t.set_font(FONT_BODY)

    avatar = fetch_avatar()
    if not (avatar and paste_avatar(t, avatar)):
        # Offline or unsupported build: keep the ASCII logo from the README.
        t.gen_text(NEOFETCH_ART, 2)


def profile_details(t: "gifos.Terminal") -> None:
    """Contact + (optional) live GitHub stats — needs GITHUB_TOKEN for stats."""
    details = f"""
    {C_BADGE}{HANDLE}@GitHub{C_RESET}
    --------------
    {C_SECONDARY}Role:     {C_TERTIARY}Software Engineer @ Pexus Tech{C_RESET}
    {C_SECONDARY}Org:      {C_TERTIARY}ING Consulting (Innovate Nepal Group){C_RESET}
    {C_SECONDARY}Location: {C_TERTIARY}Kathmandu, Nepal (UTC+5:45){C_RESET}
    {C_SECONDARY}Also:     {C_TERTIARY}External Project Supervisor{C_RESET}

    {C_BADGE}Contact:{C_RESET}
    --------------
    {C_SECONDARY}Site:     {C_TERTIARY}roshanaryanmajhi.com.np{C_RESET}
    {C_SECONDARY}GitHub:   {C_TERTIARY}github.com/if1eight0sty{C_RESET}
    {C_SECONDARY}LinkedIn: {C_TERTIARY}linkedin.com/in/if1eight0sty{C_RESET}
    {C_SECONDARY}X:        {C_TERTIARY}x.com/if1eight0sty{C_RESET}
    """
    t.gen_text(details, 2, 33, count=5, contin=True)

    # Live stats are optional: gifos hard-fails without a token, so gate on it.
    if os.environ.get("GITHUB_TOKEN"):
        _render_stats(t)



def _render_stats(t: "gifos.Terminal") -> None:
    """Live GitHub stats. Requires GITHUB_TOKEN; silently skipped otherwise."""
    try:
        stats = gifos.utils.fetch_github_stats(HANDLE)
        t.gen_text(
            f"{C_SECONDARY}Top Languages: {C_TERTIARY}"
            f"{', '.join(lang[0] for lang in stats.languages_sorted[:5])}{C_RESET}",
            16,
            33,
            count=5,
            contin=True,
        )
    except BaseException as exc:  # gifos raises non-Exception errors here
        print(f"WARNING: stats skipped ({exc})")


def main() -> None:
    # Fall back to the package default if the bundled font is unavailable.
    terminal_args = (750, 500, 15, 15) if not FONT_BODY else (750, 500, 15, 15, FONT_BODY, 15)
    t = gifos.Terminal(*terminal_args)
    # gifos defaults the prompt to "x0rzavi@gifos"; set ours explicitly.
    t.set_prompt("\x1b[0;91mroshan\x1b[0m@\x1b[0;93mif1eight0sty ~> \x1b[0m")

    boot_sequence(t)
    splash(t)
    login(t)
    fetch(t)
    profile_details(t)

    t.gen_prompt(t.curr_row)
    t.gen_typing_text(
        f"\x1b[92m# Build systems that stay boring. Thanks for stopping by!{C_RESET}",
        t.curr_row,
        contin=True,
    )
    t.gen_text("", t.curr_row, count=45, contin=True)

    t.gen_gif()
    print("INFO: output.gif written")
    update_readme()


README_PATH = "README.md"
GIF_START = "<!-- terminal-gif:start -->"
GIF_END = "<!-- terminal-gif:end -->"


NEOFETCH_START = "<!-- neofetch-art:start -->"
NEOFETCH_END = "<!-- neofetch-art:end -->"

NEOFETCH_INFO = [
    f"{HOST}",
    "--------------------------",
    "OS:       if1eight0sty 24.04 LTS",
    "Role:     Software Engineer @ Pexus Tech",
    "Org:      ING Consulting (Innovate Nepal Group)",
    "Editor:   IFIEIGHT0STY_IDE",
    "Stack:    React · TS · Node · PG",
    "Location: Kathmandu, Nepal (UTC+5:45)",
    "Also:     External Project Supervisor",
    "Status:   open to software engineer roles",
]


def avatar_ascii(path: Path, width: int = 30, gamma: float = 0.75) -> list[str]:
    """Render an image as monochrome ASCII (a code fence cannot hold a real image)."""
    image = ImageOps.autocontrast(Image.open(path).convert("L"))
    height = max(8, round(width * image.height / image.width * 0.5))
    image = image.resize((width, height))
    pixels = image.load()
    ramp = " .:-=+*#%@"
    lines = []
    for y in range(height):
        row = "".join(
            ramp[min(len(ramp) - 1, int((pixels[x, y] / 255) ** gamma * (len(ramp) - 1)))]
            for x in range(width)
        )
        lines.append(row.rstrip())
    return lines


def build_neofetch_block(avatar: Path | None) -> str:
    art = avatar_ascii(avatar) if avatar else NEOFETCH_ART.strip("\n").split("\n")
    pad = max(len(line) for line in art) + 3
    rows = []
    for i, line in enumerate(art):
        label = NEOFETCH_INFO[i - 1] if 1 <= i <= len(NEOFETCH_INFO) else ""
        rows.append((line.ljust(pad) + label).rstrip())

    return (
        "```console\n"
        f"{HOST} ~ $ neofetch\n\n"
        + "\n".join(rows)
        + f"\n\n{HOST} ~ $ whoami\n"
        "Roshan Aryan Majhi — also known online as Roshan Majhi / if1eight0sty.\n"
        "I build durable full-stack systems and developer tooling: React, TanStack,\n"
        "Nuxt and Laravel, with an allergy to demoware.\n\n"
        f"{HOST} ~ $ uptime\n"
        "99.98% — small commits, real users, fast feedback.\n"
        "```"
    )


def replace_between(content: str, start: str, end: str, snippet: str) -> str:
    if start in content and end in content:
        return content[: content.index(start)] + snippet + content[content.index(end) + len(end) :]
    return snippet + "\n\n" + content


def update_readme() -> None:
    """Inject the GIF into README.md between the markers, without touching the rest.

    If the markers are missing they are added above the existing content, so the
    hand-written README is never destroyed.
    """
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z")
    snippet = f"""{GIF_START}
<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./output.gif" />
  <source media="(prefers-color-scheme: light)" srcset="./output.gif" />
  <img alt="{HOST} terminal" src="./output.gif" />
</picture>

<sub><i>Generated with <a href="https://github.com/x0rzavi/github-readme-terminal">x0rzavi/github-readme-terminal</a> on {now}</i></sub>

</div>
{GIF_END}"""

    path = Path(README_PATH)
    if not path.exists():
        path.write_text(snippet + "\n")
        print(f"INFO: {README_PATH} created")
        return

    content = path.read_text()
    content = replace_between(content, GIF_START, GIF_END, snippet)
    avatar = AVATAR_PATH if AVATAR_PATH.exists() else None
    neofetch = f"{NEOFETCH_START}\n{build_neofetch_block(avatar)}\n{NEOFETCH_END}"
    content = replace_between(content, NEOFETCH_START, NEOFETCH_END, neofetch)
    path.write_text(content)
    print(f"INFO: {README_PATH} updated (gif + neofetch ascii)")


if __name__ == "__main__":
    main()
