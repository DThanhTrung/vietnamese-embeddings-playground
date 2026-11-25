"""Wikidata SPARQL scraper: thu thập thực thể + mã/từ viết tắt theo nhóm đối tượng."""

from .collector import collect_abbreviations

__all__ = ["collect_abbreviations"]
__version__ = "0.1.0"