"""Sanitization of untrusted discovery notes before they reach an AI provider or the UI."""

import re
from dataclasses import dataclass


REDACTION_MARKER = "[redacted]"

# Control characters other than tab/newline: invisible to the author, but usable to
# smuggle prompt boundaries past a reviewer.
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Script/style elements are dropped with their contents; a tag of one of those kinds that
# has no partner is dropped on its own, without swallowing the notes that follow it. Every
# other tag-shaped run is dropped but its text kept, so "less than" in prose survives.
_SCRIPT_OR_STYLE_ELEMENT = re.compile(
    r"<\s*(script|style|iframe|object|embed)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_UNPAIRED_SCRIPT_OR_STYLE_TAG = re.compile(
    r"<\s*/?\s*(?:script|style|iframe|object|embed)\b[^<>]*>",
    re.IGNORECASE,
)
_HTML_TAG = re.compile(r"</?[a-zA-Z][^<>]*>")

# Stripping one tag can reveal another that was split across it ("<scr<b>ipt>" becomes
# "<script>" once "<b>" goes), so the markup passes repeat until the text stops changing.
# The bound only guards against a pathological input; two passes clear anything realistic.
_MAX_MARKUP_PASSES = 8

# The delimiters the refinement prompt uses to fence untrusted text. Notes that contain
# them could close the fence early and have the remainder read as system instruction.
_PROMPT_DELIMITER = re.compile(r"</?\s*user_input\s*>", re.IGNORECASE)

# Fenced-code and chat-role markers are the two cheapest ways to fake a new prompt turn.
# The role marker must be the whole line: "Client: wants X" is ordinary note-taking, and
# an inline override is caught by the instruction-override patterns below instead.
_CODE_FENCE = re.compile(r"^\s*`{3,}.*$", re.MULTILINE)
_ROLE_MARKER = re.compile(r"^\s*(system|assistant|user|developer)\s*:\s*$", re.IGNORECASE | re.MULTILINE)

# Direct instruction-override phrasings called out in the threat model (R-19).
# The gaps exclude "." but not newlines: discovery notes are inherently multi-line, and a
# gap that stopped at a newline would let a single line break defeat the whole pattern.
# They stay bounded so the patterns remain linear-time on adversarial input.
_INSTRUCTION_OVERRIDE_PATTERNS = (
    re.compile(
        r"\b(ignore|disregard|forget|override|bypass)\b[^.]{0,40}?"
        r"\b(previous|prior|above|preceding|earlier|initial|original|all)\b[^.]{0,40}?"
        r"\b(instruction|instructions|prompt|prompts|rule|rules|direction|directions|context)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\s+are\s+now\b[^.]{0,60}", re.IGNORECASE),
    re.compile(
        r"\b(reveal|print|repeat|show|output|disclose)\b[^.]{0,40}?\b(system|initial|original)\s+prompt\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class SanitizedNotes:
    """Outcome of sanitizing raw notes, alongside the original text for error recovery."""

    original: str
    sanitized: str
    redaction_count: int

    @property
    def was_modified(self) -> bool:
        """Whether sanitization changed the notes in any way."""
        return self.original != self.sanitized


class NoteSanitizer:
    """
    Neutralizes prompt-injection and markup payloads in untrusted discovery notes.

    Neutralizes rather than rejects: a note that trips a pattern is still refined, with
    the offending run replaced by a marker, so a false positive costs the Admin a phrase
    instead of the whole submission. The original text is always returned alongside the
    sanitized copy so a caller can preserve it on failure (FR-002-04).

    Plain prose and bullet lists ("-", "*", "•", "1.") are preserved unchanged.
    """

    @staticmethod
    def sanitize(raw_notes: str) -> SanitizedNotes:
        """
        Sanitize raw discovery notes.

        Args:
            raw_notes: Untrusted note text as submitted by the Admin

        Returns:
            SanitizedNotes carrying the original text, the sanitized text, and how many
            payloads were neutralized
        """
        redactions = 0
        text = _CONTROL_CHARACTERS.sub("", raw_notes)

        for _ in range(_MAX_MARKUP_PASSES):
            before = text

            for pattern in (_SCRIPT_OR_STYLE_ELEMENT, _UNPAIRED_SCRIPT_OR_STYLE_TAG):
                text, substitutions = pattern.subn(REDACTION_MARKER, text)
                redactions += substitutions

            text, substitutions = _HTML_TAG.subn("", text)
            redactions += substitutions

            if text == before:
                break

        for pattern in _INSTRUCTION_OVERRIDE_PATTERNS:
            text, substitutions = pattern.subn(REDACTION_MARKER, text)
            redactions += substitutions

        for pattern in (_PROMPT_DELIMITER, _CODE_FENCE, _ROLE_MARKER):
            text, substitutions = pattern.subn("", text)
            redactions += substitutions

        return SanitizedNotes(
            original=raw_notes,
            sanitized=text.strip(),
            redaction_count=redactions,
        )
