from abc import ABC, abstractmethod
from typing import Any
import os
from pathlib import Path
from app.core.exceptions import (
    DocumentNotFoundError,
    UnsupportedFileTypeError,
    PermissionDeniedError,
    AgentEngineError,
)


class BaseDocumentParser(ABC):
    SUPPORTED_EXTENSIONS: list[str] = []

    def validate_path(self, file_path: str) -> str:
        real_path = os.path.realpath(file_path)
        if not os.path.exists(real_path):
            raise DocumentNotFoundError(f"File not found: {file_path}")
        if not os.path.isfile(real_path):
            raise UnsupportedFileTypeError(f"Not a file: {file_path}")
        return real_path

    def safe_parse(self, file_path: str, **kwargs) -> dict:
        try:
            real_path = self.validate_path(file_path)
            return self.parse(real_path, **kwargs)
        except (FileNotFoundError, DocumentNotFoundError):
            raise
        except PermissionError:
            raise PermissionDeniedError(f"Permission denied: {file_path}")
        except ValueError:
            raise
        except Exception as e:
            raise AgentEngineError(f"Failed to parse {file_path}: {str(e)}")

    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> dict:
        pass
