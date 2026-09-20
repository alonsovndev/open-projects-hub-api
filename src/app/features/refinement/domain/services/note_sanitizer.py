"""Sanitization of untrusted discovery notes before they reach an AI provider or the UI."""

import re
from dataclasses import dataclass


REDACTION_MARKER = "[redacted]"

# Control characters other than tab/newline: invisible to the author, but usable to
# smuggle prompt boundaries past a reviewer.
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Script/style elements are dropped with their contents; every other tag-shaped run is
# dropped but its text kept, so "less than" comparisons in prose survive.
_SCRIPT_OR_STYLE_ELEMENT = re.compile(
    r"<\s*(script|style|iframe|object|embed)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_UNCLOSED_SCRIPT_OR_STYLE = re.compile(
    r"<\s*(script|style|iframe|object|embed)\b[^>]*>.*",
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAG = re.compile(r"</?[a-zA-Z][^<>]*>")

# The delimiters the refinement prompt uses to fence untrusted text. Notes that contain
# them could close the fence early and have the remainder read as system instruction.
_PROMPT_DELIMITER = re.compile(r"</?\s*user_input\s*>", re.IGNORECASE)

# Fenced-code and chat-role markers are the two cheapest ways to fake a new prompt turn.
# The role marker must be the whole line: "Client: wants X" is ordinary note-taking, and
# an inline override is caught by the instruction-override patterns below instead.
_CODE_FENCE = re.compile(r"^\s*`{3,}.*$", re.MULTILINE)
_ROLE_MARKER = re.compile(r"^\s*(system|assistant|user|developer)\s*:\s*$", re.IGNORECASE | re.MULTILINE)

# Direct instruction-override phrasings called out in the threat model (R-19).
_INSTRUCTION_OVERRIDE_PATTERNS = (
    re.compile(
        r"\b(ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}?"
        r"\b(previous|prior|above|preceding|earlier|initial|original|all)\b[^.\n]{0,40}?"
        r"\b(instruction|instructions|prompt|prompts|rule|rules|direction|directions|context)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\s+are\s+now\b[^.\n]{0,60}", re.IGNORECASE),
    re.compile(
        r"\b(reveal|print|repeat|show|output|disclose)\b[^.\n]{0,40}?\b(system|initial|original)\s+prompt\b",
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

        for pattern in (_SCRIPT_OR_STYLE_ELEMENT, _UNCLOSED_SCRIPT_OR_STYLE, *_INSTRUCTION_OVERRIDE_PATTERNS):
            text, substitutions = pattern.subn(REDACTION_MARKER, text)
            redactions += substitutions

        for pattern in (_HTML_TAG, _PROMPT_DELIMITER, _CODE_FENCE, _ROLE_MARKER):
            text, substitutions = pattern.subn("", text)
            redactions += substitutions

        return SanitizedNotes(
            original=raw_notes,
            sanitized=text.strip(),
            redaction_count=redactions,
        )
