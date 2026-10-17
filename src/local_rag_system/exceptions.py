"""Domain exceptions, translated to HTTP responses in :mod:`main`."""


class RagError(Exception):
    """Base class for all application errors."""


class UnsupportedFileTypeError(RagError):
    """The uploaded file has an extension we cannot ingest."""


class FileTooLargeError(RagError):
    """The uploaded file exceeds the configured size limit."""


class EmptyDocumentError(RagError):
    """No text could be extracted from the uploaded file."""


class InvalidChunkingError(RagError):
    """Chunk size / overlap combination is invalid."""


class DocumentNotFoundError(RagError):
    """The requested document does not exist."""


class ConversationNotFoundError(RagError):
    """The requested conversation does not exist."""


class WebSearchError(RagError):
    """The web search provider failed or is unreachable."""


class ModelNotFoundError(RagError):
    """The requested Ollama model is not available locally."""


class OllamaUnavailableError(RagError):
    """The Ollama server cannot be reached."""
