"""
SkillSync — Analyzer Module
Responsibility: NLP processing and semantic similarity scoring.
"""

import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class AnalyzerError(Exception):
    """Raised when the analyzer cannot process the given input."""


class ScoringEngine:
    """
    Compares a parsed resume against a job description using
    spaCy vectors and cosine similarity.

    Attributes:
        nlp: Loaded spaCy language model.
    """

    MODEL = "en_core_web_md"

    def __init__(self):
        try:
            self.nlp = spacy.load(self.MODEL)
        except OSError:
            raise AnalyzerError(
                f"spaCy model '{self.MODEL}' not found. "
                f"Run: python -m spacy download {self.MODEL}"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, resume_text: str, job_text: str) -> dict:
        """
        Compares resume against job description.

        Returns a structured result dict with:
            - score         : float (0-100)
            - strong        : list of strongly matched keywords
            - partial       : list of partially matched keywords
            - missing       : list of missing keywords
            - recommendation: str
        """
        if not resume_text.strip():
            raise AnalyzerError("Resume text is empty.")
        if not job_text.strip():
            raise AnalyzerError("Job description text is empty.")

        resume_doc = self.nlp(resume_text.lower())
        job_doc    = self.nlp(job_text.lower())

        # Overall semantic score
        overall = self._cosine_score(resume_doc, job_doc)

        # Keyword-level breakdown
        job_keywords = self._extract_keywords(job_doc)
        strong, partial, missing = self._classify_keywords(
            job_keywords, resume_doc
        )

        return {
            "score"          : round(overall * 100, 1),
            "strong"         : strong,
            "partial"        : partial,
            "missing"        : missing,
            "recommendation" : self._recommend(overall, missing),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_score(doc_a, doc_b) -> float:
        """Cosine similarity between two spaCy doc vectors."""
        vec_a = doc_a.vector.reshape(1, -1)
        vec_b = doc_b.vector.reshape(1, -1)
        return float(cosine_similarity(vec_a, vec_b)[0][0])

    def _extract_keywords(self, doc) -> list[str]:
        """
        Extract meaningful keywords from the job description:
        nouns, proper nouns, and adjectives that are not stopwords.
        """
        seen = set()
        keywords = []
        for token in doc:
            if (
                token.pos_ in {"NOUN", "PROPN", "ADJ"}
                and not token.is_stop
                and not token.is_punct
                and len(token.text) > 2
            ):
                lemma = token.lemma_.strip()
                if lemma and lemma not in seen:
                    seen.add(lemma)
                    keywords.append(lemma)
        return keywords

    def _classify_keywords(
        self, keywords: list[str], resume_doc
    ) -> tuple[list, list, list]:
        """
        For each job keyword, compute similarity against the full
        resume doc vector and classify:
            strong  : similarity >= 0.75
            partial : similarity >= 0.45
            missing : similarity <  0.45
        """
        strong, partial, missing = [], [], []

        resume_vec = resume_doc.vector.reshape(1, -1)

        for kw in keywords:
            token_doc = self.nlp(kw)
            if not token_doc.has_vector:
                continue
            kw_vec = token_doc.vector.reshape(1, -1)
            sim = float(cosine_similarity(kw_vec, resume_vec)[0][0])

            if sim >= 0.75:
                strong.append(kw)
            elif sim >= 0.45:
                partial.append(kw)
            else:
                missing.append(kw)

        return strong, partial, missing

    @staticmethod
    def _recommend(score: float, missing: list[str]) -> str:
        if score >= 0.85:
            return "Excellent match. Your resume aligns strongly with this role."
        elif score >= 0.70:
            top = ", ".join(missing[:3]) if missing else "none identified"
            return f"Good match. Consider adding: {top}."
        elif score >= 0.50:
            top = ", ".join(missing[:5]) if missing else "none identified"
            return f"Moderate match. Strengthen your resume with: {top}."
        else:
            top = ", ".join(missing[:5]) if missing else "none identified"
            return f"Low match. Significant gaps found. Focus on: {top}."