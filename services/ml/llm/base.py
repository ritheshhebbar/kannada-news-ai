from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseSummarizer(ABC):
    """Abstract base class for English news summarization."""

    @abstractmethod
    def summarize(self, numbered_sentences: List[str]) -> Dict[str, Any]:
        """Generate headline, summary, cited key points, and key facts from numbered sentences."""
        pass
