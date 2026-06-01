"""OCR adapter for image text extraction."""
from typing import Optional


class OCRAdapter:
    """Base OCR adapter interface."""

    async def recognize(self, image_bytes: bytes, language: str = "chi+eng") -> dict:
        """Extract text from image bytes.

        Returns:
            {"text": str, "confidence": float, "language": str}
        """
        raise NotImplementedError


class TesseractOCRAdapter(OCRAdapter):
    """Tesseract-based OCR adapter."""

    def __init__(self, tesseract_cmd: str = "tesseract"):
        self.cmd = tesseract_cmd

    async def recognize(self, image_bytes: bytes, language: str = "chi+eng") -> dict:
        """Extract text using Tesseract OCR."""
        import asyncio
        import subprocess
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(image_bytes)
            tmp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                self.cmd, tmp_path, "stdout",
                "-l", language,
                "--psm", "6",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            text = stdout.decode("utf-8", errors="ignore").strip()

            # Get confidence via tsv output
            proc2 = await asyncio.create_subprocess_exec(
                self.cmd, tmp_path, "stdout",
                "-l", language,
                "--psm", "6",
                "--oem", "3",
                "tsv",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout2, _ = await proc2.communicate()
            lines = stdout2.decode("utf-8", errors="ignore").strip().split("\n")
            confidences = []
            for line in lines[1:]:  # skip header
                parts = line.split("\t")
                if len(parts) >= 11:
                    try:
                        conf = float(parts[10])
                        if conf > 0:
                            confidences.append(conf)
                    except ValueError:
                        pass

            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

            return {
                "text": text,
                "confidence": avg_confidence,
                "language": language,
            }
        finally:
            os.unlink(tmp_path)


class PaddleOCRAdapter(OCRAdapter):
    """PaddleOCR-based adapter (placeholder for future implementation)."""

    async def recognize(self, image_bytes: bytes, language: str = "ch") -> dict:
        raise NotImplementedError("PaddleOCR adapter not yet implemented")
