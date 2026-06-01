from app.engines.knowledge_engine.parser.base import BaseDocumentParser


class PDFParser(BaseDocumentParser):
    SUPPORTED_EXTENSIONS = [".pdf"]

    def parse(self, file_path: str, **kwargs) -> dict:
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text_parts = []
            tables = []
            ocr_adapter = kwargs.get("ocr_adapter")

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()

                # K-017: If page has no text (scanned), use OCR
                if not page_text.strip() and ocr_adapter:
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        # Can't await in sync context; skip OCR for now
                        pass
                    else:
                        import asyncio
                        result = asyncio.run(ocr_adapter.recognize(img_bytes))
                        page_text = result.get("text", "")

                text_parts.append(page_text)
                for table in page.find_tables():
                    tables.append(table.extract())

            doc.close()
            return {
                "content": "\n".join(text_parts),
                "tables": tables,
                "metadata": {"pages": len(doc), "format": "pdf"},
            }
        except ImportError:
            with open(file_path, "rb") as f:
                content = f.read()
            return {"content": str(content), "tables": [], "metadata": {"format": "pdf"}}
