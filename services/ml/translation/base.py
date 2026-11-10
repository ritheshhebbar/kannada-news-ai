from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseTranslator(ABC):
    """Abstract base class for Kannada-to-English translation models."""

    @abstractmethod
    def translate_sentences(self, sentences: List[str]) -> List[str]:
        """Translate a batch of sentence-level Kannada texts into English."""
        pass

    @abstractmethod
    def translate_headline(self, headline: str) -> str:
        """Translate a headline with telegraphic news style."""
        pass

