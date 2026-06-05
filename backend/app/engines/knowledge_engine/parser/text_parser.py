import logging

from app.engines.knowledge_engine.parser.base import BaseDocumentParser

logger = logging.getLogger(__name__)


class TextParser(BaseDocumentParser):
    SUPPORTED_EXTENSIONS = [".txt", ".csv", ".html", ".htm", ".md", ".json", ".xml"]

    def parse(self, file_path: str, **kwargs) -> dict:
        ext = file_path.rsplit(".", 1)[-1].lower()
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        metadata = {"format": ext, "length": len(content)}

        if ext in ("html", "htm"):
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(content, "html.parser")
                content = soup.get_text(separator="\n", strip=True)
            except ImportError:
                logger.debug("BeautifulSoup not available, skipping HTML parsing")
        elif ext == "csv":
            import csv
            import io

            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            metadata["rows"] = len(rows)

        return {"content": content, "metadata": metadata}
