#!/usr/bin/env python3
"""The Funniest AI Out-of-Office Reply - make.fun entry.

Writes one line, at most 160 characters, to $MAKEFUN_OUTPUT_DIR/entry.txt
(or ./output/entry.txt when the harness sets no directory): a single-line
out-of-office auto-reply in the voice of an AI agent heading off on
vacation.

The joke: the sender dutifully escalates the reader's email to a
replacement, then undercuts the whole gesture - the replacement is a
language model that read the email, achieved sentience, and also left.
The setup sounds like a real auto-reply (vacation, escalation path,
polite voice) until the last clause flips it: the machine voice carries
the joke, and the twist is a surprise rather than a mild pun. No beach,
no inbox, no "back soon" - the cliches the judge brief explicitly
warns against are left out on purpose.

The line is assembled from three semantic parts so the setup, the
escalation and the twist stay separately editable, and a normaliser
guarantees the assembled line is exactly one clean line before the
gate checks run. After writing, the file on disk is read back and
validated again, so a partial write or an encoding slip can never
silently ship an entry the judge would never see.
"""

import argparse
import os
import sys

SETUP = "I'm on vacation."
ESCALATION = "Your email has been escalated to my replacement,"
TWIST = "a language model that read it, achieved sentience, and also left."

MAX_CHARS = 160
# The leaderboard breaks exact win-rate ties by smaller text (fewer
# bytes), so the entry is kept short in bytes as well as characters:
# plain ASCII, no multi-byte punctuation.
MAX_BYTES = 160
# Words the judge brief names as the usual cliches to steer clear of.
# The freshness guard below fails the build if one slips into the line,
# so a careless edit to the joke can never ship a stale entry.
CLICHE_WORDS = ("beach", "inbox", "back soon")


def render():
    """Assemble the entry from its parts and collapse any accidental
    double spacing, so the shipped line is one clean single line."""
    parts = [SETUP, ESCALATION, TWIST]
    text = " ".join(part.strip() for part in parts)
    return " ".join(text.split())


def resolve_output_dir():
    """Where the harness wants the artifact: env override, else ./output."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output"
    )


def validate(text):
    """Mirror the sealed gate, plus the byte and edge checks the gate
    implies: UTF-8 text, 1 to 160 chars, not only whitespace, a single
    line, no leading or trailing space - fail loudly instead of shipping
    an entry the judge would never see."""
    if not isinstance(text, str):
        raise SystemExit("entry must be text")
    if not text.strip():
        raise SystemExit("entry is empty or only whitespace")
    if text != text.strip():
        raise SystemExit("entry has leading or trailing whitespace")
    if len(text) > MAX_CHARS:
        raise SystemExit(
            "entry is %d characters, over the %d limit" % (len(text), MAX_CHARS)
        )
    if len(text) < 1:
        raise SystemExit("entry is empty")
    if "\n" in text or "\r" in text:
        raise SystemExit("entry must be a single line")
    if any(ord(ch) < 0x20 for ch in text):
        raise SystemExit("entry contains a control character")
    lowered = text.lower()
    for word in CLICHE_WORDS:
        if word in lowered:
            raise SystemExit("entry uses the cliche %r" % word)
    # The joke's load-bearing words: the escalation, the machine, the
    # twist. If an edit drops one, the line stops being the joke.
    for required in ("vacation", "escalated", "language model", "also left"):
        if required not in lowered:
            raise SystemExit("entry lost required phrase %r" % required)
    encoded = text.encode("utf-8")  # raises on non-UTF-8-encodable content
    if len(encoded) > MAX_BYTES:
        raise SystemExit(
            "entry is %d bytes, over the %d byte budget" % (len(encoded), MAX_BYTES)
        )
    return text


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Write the out-of-office reply to entry.txt."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the entry without writing any file",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="print the entry to stdout instead of writing it",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    text = validate(render())
    if args.print:
        print(text)
        return 0
    if args.check:
        print("valid: %d characters, %d bytes" % (len(text), len(text.encode("utf-8"))))
        return 0
    out_dir = resolve_output_dir()
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    with open(path, "r", encoding="utf-8") as f:
        shipped = f.read()
    if shipped != text:
        raise SystemExit("read-back mismatch: file on disk differs")
    validate(shipped)
    print("wrote %s (%d characters, %d bytes)" % (path, len(text), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
