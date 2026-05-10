import sys
import time
import os
import random
import math
import datetime

# ─── ANSI ────────────────────────────────────────────────────────────────────

R  = "\033[0m"
B  = "\033[1m"
D  = "\033[2m"
IT = "\033[3m"

def fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
def bg(r,g,b): return f"\033[48;2;{r};{g};{b}m"

GOLD   = fg(255,215,0)
SILVER = fg(180,180,200)
BLOOD  = fg(180,30,30)
SMOKE  = fg(120,120,140)
WHITE  = fg(240,240,245)
JADE   = fg(0,200,140)
VIOLET = fg(160,80,220)
RESET  = R

def tw() -> int:
    try: return os.get_terminal_size().columns
    except OSError: return 80

def color(text, *codes): return "".join(codes) + text + RESET

# ─── Data ────────────────────────────────────────────────────────────────────

# Each entry: (title, year, director, genre_tag, short_synopsis)
FILMS = [
    ("Stalker",                  1979, "Andrei Tarkovsky",   "METAPHYSICAL",
     "Three men enter a forbidden zone where the innermost wish of any visitor is granted — or so it is said."),
    ("Mulholland Drive",         2001, "David Lynch",        "SURREALIST",
     "A woman wakes in Los Angeles with no memory. The city around her is a dream eating itself."),
    ("Persona",                  1966, "Ingmar Bergman",     "PSYCHOLOGICAL",
     "An actress falls silent. Her nurse speaks. Slowly the boundary between them dissolves."),
    ("2001: A Space Odyssey",    1968, "Stanley Kubrick",    "COSMIC",
     "Mankind stands at the threshold of the infinite, guided and betrayed by its own tools."),
    ("The Turin Horse",          2011, "Béla Tarr",          "NIHILIST",
     "After Nietzsche embraced a beaten horse on a Turin street, the world began to end. This is the end."),
    ("Jeanne Dielman",           1975, "Chantal Akerman",    "DURATIONAL",
     "Three days. Potatoes. Silence. The slow collapse of a woman inside the architecture of routine."),
    ("Mirror",                   1975, "Andrei Tarkovsky",   "LYRICAL",
     "Memory, dream, and documentary footage bleed into each other. A life becomes a landscape."),
    ("Eraserhead",               1977, "David Lynch",        "INDUSTRIAL",
     "A man in an industrial wasteland raises a child who should not exist."),
    ("Aguirre, the Wrath of God",1972, "Werner Herzog",      "CONQUEST",
     "A conquistador drifts down the Amazon on a raft of ambition, madness, and monkeys."),
    ("Come and See",             1985, "Elem Klimov",        "WAR",
     "A boy walks into the Second World War and watches his own face age a hundred years."),
    ("Playtime",                 1967, "Jacques Tati",       "ARCHITECTURAL",
     "Paris has been replaced by glass and steel. Monsieur Hulot is lost in it. So is modernity."),
    ("Holy Motors",              2012, "Leos Carax",         "METAMORPHIC",
     "A man in a white limousine travels the city performing lives — each one someone else's truth."),
    ("The Colour of Pomegranates",1969,"Sergei Parajanov",   "ICONOGRAPHIC",
     "Biography as tableau. The poet Sayat-Nova rendered in wool, blood, pomegranate, and silence."),
    ("L'Avventura",              1960, "Michelangelo Antonioni","ALIENATION",
     "A woman disappears on a volcanic island. The search becomes the film. The film forgets her."),
    ("Sans Soleil",              1983, "Chris Marker",       "ESSAY",
     "Letters from a cameraman to a woman who receives them. Memory as the only true geography."),
    ("Week End",                 1967, "Jean-Luc Godard",    "APOCALYPTIC",
     "A couple drives into the French countryside. The road becomes a ruin of modernity."),
    ("Andrei Rublev",            1966, "Andrei Tarkovsky",   "SPIRITUAL",
     "A 15th-century icon painter walks through war and plague, searching for the will to create."),
    ("Lost Highway",             1997, "David Lynch",        "NOIRISH",
     "A man receives a video of his own murder. Identity cracks and someone else steps through."),
    ("The Seventh Seal",         1957, "Ingmar Bergman",     "ALLEGORICAL",
     "A knight returning from the Crusades plays chess with Death on a grey Baltic beach."),
    ("Satantango",               1994, "Béla Tarr",          "ELEGY",
     "Seven hours. Rain. A collective farm collapses. A messiah may or may not return."),
]

GENRES_COLOR = {
    "METAPHYSICAL": fg(100,180,255),
    "SURREALIST":   fg(220,120,240),
    "PSYCHOLOGICAL":fg(240,160,80),
    "COSMIC":       fg(80,200,255),
    "NIHILIST":     fg(160,160,160),
    "DURATIONAL":   fg(180,220,140),
    "LYRICAL":      fg(255,200,100),
    "INDUSTRIAL":   fg(200,100,80),
    "CONQUEST":     fg(240,100,100),
    "WAR":          BLOOD,
    "ARCHITECTURAL":fg(100,240,200),
    "METAMORPHIC":  VIOLET,
    "ICONOGRAPHIC": GOLD,
    "ALIENATION":   SILVER,
    "ESSAY":        fg(180,240,180),
    "APOCALYPTIC":  fg(255,100,60),
    "SPIRITUAL":    fg(200,220,255),
    "NOIRISH":      fg(140,140,180),
    "ALLEGORICAL":  fg(220,200,120),
    "ELEGY":        fg(160,180,210),
}

# ─── Rendering helpers ────────────────────────────────────────────────────────

def wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines, cur, length = [], [], 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if length + add > width:
            lines.append(" ".join(cur))
            cur, length = [w], len(w)
        else:
            cur.append(w)
            length += add
    if cur: lines.append(" ".join(cur))
    return lines

def center(text: str, width: int, fill=" ") -> str:
    l = len(text)
    left = (width - l) // 2
    right = width - l - left
    return fill*left + text + fill*right

def hr(width: int, ch="─", col=SMOKE) -> str:
    return color(ch * width, col)

# ─── Animated spinner ─────────────────────────────────────────────────────────

REEL = ["◐","◓","◑","◒"]

def spin(msg: str, duration: float = 1.0) -> None:
    end = time.time() + duration
    i = 0
    while time.time() < end:
        frame = color(REEL[i % len(REEL)], GOLD)
        sys.stdout.write(f"\r  {frame}  {color(msg, SMOKE, D)}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write("\r" + " " * (len(msg) + 8) + "\r")
    sys.stdout.flush()

# ─── Typewriter ───────────────────────────────────────────────────────────────

def typewrite(text: str, delay: float = 0.022) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()

# ─── Film card ────────────────────────────────────────────────────────────────

def render_card(film: tuple) -> None:
    title, year, director, genre, synopsis = film
    W = min(tw(), 76)
    inner = W - 4
    gcol  = GENRES_COLOR.get(genre, WHITE)

    # border chars
    TL,TR,BL,BR = "╔","╗","╚","╝"
    H,V = "═","║"
    ML,MR = "╠","╣"

    top    = color(TL + H*(W-2) + TR, GOLD)
    mid    = color(ML + H*(W-2) + MR, GOLD)
    bot    = color(BL + H*(W-2) + BR, GOLD)
    vbar   = color(V, GOLD)
    blank  = f"{vbar} {' '*inner} {vbar}"

    genre_badge  = f"[ {genre} ]"
    title_str    = f"{title}  ({year})"
    director_str = f"dir. {director}"

    title_lines  = wrap(title_str, inner)
    syn_lines    = wrap(synopsis,  inner)

    def row(text, *codes, align="left"):
        clean_len = len(text)
        pad = inner - clean_len
        if align == "center":
            lp = pad // 2
            rp = pad - lp
            rendered = " "*lp + color(text, *codes) + " "*rp
        else:
            rendered = color(text, *codes) + " "*pad
        return f"{vbar} {rendered} {vbar}"

    print()
    print(top)
    print(blank)

    # Genre badge centered
    badge_lp = (inner - len(genre_badge)) // 2
    badge_rp = inner - len(genre_badge) - badge_lp
    badge_rendered = " "*badge_lp + color(genre_badge, gcol, B) + " "*badge_rp
    print(f"{vbar} {badge_rendered} {vbar}")

    print(blank)
    print(mid)
    print(blank)

    # Title
    for i, line in enumerate(title_lines):
        lp = (inner - len(line)) // 2
        rp = inner - len(line) - lp
        rendered = " "*lp + color(line, GOLD, B) + " "*rp
        print(f"{vbar} {rendered} {vbar}")

    # Director
    dir_lp = (inner - len(director_str)) // 2
    dir_rp = inner - len(director_str) - dir_lp
    dir_rendered = " "*dir_lp + color(director_str, SILVER, IT) + " "*dir_rp
    print(f"{vbar} {dir_rendered} {vbar}")

    print(blank)
    print(mid)
    print(blank)

    # Synopsis
    for line in syn_lines:
        pad = inner - len(line)
        rendered = color(line, WHITE) + " "*pad
        print(f"{vbar} {rendered} {vbar}")

    print(blank)
    print(bot)
    print()

# ─── Rating UI ────────────────────────────────────────────────────────────────

RATINGS: dict[str, int] = {}   # title → 1..5

def stars(n: int) -> str:
    return color("★"*n, GOLD) + color("☆"*(5-n), SMOKE)

def prompt_rating(title: str) -> None:
    print(color("  Rate this film (1–5 stars, or Enter to skip): ", JADE), end="", flush=True)
    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt):
        return
    if raw in ("1","2","3","4","5"):
        n = int(raw)
        RATINGS[title] = n
        print(f"  {stars(n)}  {color('Recorded.', SMOKE, D)}")
    print()

# ─── Stats / watched list ─────────────────────────────────────────────────────

def render_stats(seen_titles: list[str]) -> None:
    if not seen_titles:
        return
    W = min(tw(), 76)
    print()
    print(color("  ╒" + "═"*(W-4) + "╕", VIOLET))
    header_text = "YOUR SCREENING RECORD"
    lp = (W-4-len(header_text))//2
    rp = W-4-len(header_text)-lp
    print(color(f"  │{' '*lp}{header_text}{' '*rp}│", VIOLET))
    print(color("  ╞" + "═"*(W-4) + "╡", VIOLET))

    for t in seen_titles:
        r = RATINGS.get(t)
        star_str = stars(r) if r else color("(unrated)", SMOKE, D)
        line = f"  {t}"
        pad  = W - 4 - len(t) - 2
        rated_display = f"  {color('│', VIOLET)} {line}{' '*max(0,pad-12)} {star_str}  {color('│', VIOLET)}"
        print(rated_display)

    print(color("  ╘" + "═"*(W-4) + "╛", VIOLET))

    if RATINGS:
        avg = sum(RATINGS.values()) / len(RATINGS)
        filled = int(round(avg))
        print()
        print(f"  {color('Average rating:', SMOKE, D)} {stars(filled)} {color(f'({avg:.1f})', JADE)}")
    print()

# ─── Header ──────────────────────────────────────────────────────────────────

ASCII_TITLE = [
    "  ░█████╗░██╗███╗░░██╗███████╗███╗░░░███╗░█████╗░",
    "  ██╔══██╗██║████╗░██║██╔════╝████╗░████║██╔══██╗",
    "  ██║░░╚═╝██║██╔██╗██║█████╗░░██╔████╔██║███████║",
    "  ██║░░██╗██║██║╚████║██╔══╝░░██║╚██╔╝██║██╔══██║",
    "  ╚█████╔╝██║██║░╚███║███████╗██║░╚═╝░██║██║░░██║",
    "  ░╚════╝░╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░░░╚═╝╚═╝░░╚═╝",
]

SUBTITLE = "T E R M I N A L   F I L M   O R A C L E"

def render_header() -> None:
    W = min(tw(), 80)
    print()
    for i, line in enumerate(ASCII_TITLE):
        t = i / max(len(ASCII_TITLE)-1, 1)
        r = int(255 * (1-t) + 80 * t)
        g = int(180 * (1-t) + 30 * t)
        b = int(0   * (1-t) + 120 * t)
        print(color(line, fg(r,g,b), B))
    print()
    sub_lp = (W - len(SUBTITLE)) // 2
    print(color(" "*sub_lp + SUBTITLE, SMOKE, D))
    W2 = min(tw(), 76)
    print(color("  " + "─"*(W2-4), SMOKE, D))
    date_str = datetime.datetime.now().strftime("%A, %d %B %Y  ·  %H:%M")
    print(color(f"  {date_str}", SMOKE, D))
    print()

# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    render_header()
    typewrite(color(
        "  The Oracle knows which films you have not yet survived. Shall we begin?",
        SMOKE, D), delay=0.018)
    print()

    pool: list[int]  = list(range(len(FILMS)))
    seen_indices: set[int] = set()
    seen_titles:  list[str] = []

    while True:
        available = [i for i in pool if i not in seen_indices]
        if not available:
            # full cycle — reshuffle
            print(color("  ── You have seen everything the Oracle holds. Cycling the reel. ──", SMOKE, D))
            print()
            seen_indices.clear()
            available = list(range(len(FILMS)))

        spin("Consulting the archive…", duration=random.uniform(0.6, 1.2))

        idx = random.choice(available)
        seen_indices.add(idx)
        film = FILMS[idx]
        seen_titles.append(film[0])

        render_card(film)
        prompt_rating(film[0])

        print(color("  [Enter]  another recommendation", JADE))
        print(color("  [s]      show your screening record", VIOLET))
        print(color("  [q]      exit the Oracle", SMOKE, D))
        print()
        print(color("  › ", JADE), end="", flush=True)
        try:
            ans = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            ans = "q"

        print()

        if ans == "q":
            render_stats(seen_titles)
            typewrite(color(
                "  The Oracle withdraws. Go. Watch something that unsettles you.",
                SMOKE, IT), delay=0.022)
            print()
            break
        elif ans == "s":
            render_stats(seen_titles)
            print(color("  [Enter] continue  ·  [q] exit", SMOKE, D))
            print(color("  › ", JADE), end="", flush=True)
            try:
                nxt = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                nxt = "q"
            print()
            if nxt == "q":
                typewrite(color(
                    "  The Oracle withdraws. Go. Watch something that unsettles you.",
                    SMOKE, IT), delay=0.022)
                print()
                break
            # else continue loop

if __name__ == "__main__":
    main()