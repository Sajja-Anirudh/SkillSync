"""
SkillSync — Parser Module
Responsibility: PDF ingestion and raw text extraction.
"""

import re
import pdfplumber


class ParserError(Exception):
    """Raised when the parser cannot process the given file."""


class Resume:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_text = ""
        self.page_count = 0

    def extract(self) -> "Resume":
        pages = self._read_pages()
        combined = "\n\n".join(pages)
        self.raw_text = self._clean(combined)
        self.page_count = len(pages)
        return self

    def _read_pages(self) -> list[str]:
        try:
            with pdfplumber.open(self.file_path) as pdf:
                pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                if not pages:
                    raise ParserError(
                        f"No extractable text in '{self.file_path}'. "
                        "PDF may be scanned or image-based."
                    )
                return pages
        except FileNotFoundError:
            raise ParserError(f"File not found: '{self.file_path}'")
        except Exception as exc:
            raise ParserError(f"Could not read '{self.file_path}': {exc}") from exc

    @staticmethod
    def _clean(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    def __repr__(self):
        status = f"{self.page_count} page(s)" if self.raw_text else "not extracted"
        return f"<Resume file='{self.file_path}' [{status}]>"