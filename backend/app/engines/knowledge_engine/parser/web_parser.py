"""
网页内容解析器
支持从 URL 抓取和解析网页内容
"""

import re
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from .base import BaseDocumentParser


@dataclass
class ParsedDocument:
    """Parsed document result."""
    content: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseParser(BaseDocumentParser):
    """Alias for BaseDocumentParser for backward compatibility."""
    pass

logger = logging.getLogger(__name__)


@dataclass
class WebPage:
    """网页数据"""
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]


class WebParser(BaseParser):
    """网页内容解析器"""

    def __init__(self):
        super().__init__()
        self.supported_types = ["web", "url", "html"]
        self.timeout = 30
        self.max_content_length = 1_000_000  # 1MB
        self.user_agent = "Mozilla/5.0 (compatible; AgentEngine/1.0)"

    async def parse(self, source: str, **kwargs) -> ParsedDocument:
        """解析网页内容"""
        url = source
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            page = await self._fetch_page(url)
            content = self._extract_content(page.content)
            title = page.title or url

            return ParsedDocument(
                content=content,
                metadata={
                    "source": "web",
                    "url": url,
                    "title": title,
                    "content_type": "text/html",
                    "fetched_at": self._get_timestamp()
                }
            )
        except Exception as e:
            logger.error(f"Failed to parse web page {url}: {e}")
            raise

    async def parse_batch(self, urls: List[str], **kwargs) -> List[ParsedDocument]:
        """批量解析网页"""
        results = []
        for url in urls:
            try:
                doc = await self.parse(url, **kwargs)
                results.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse {url}: {e}")
                results.append(ParsedDocument(
                    content="",
                    metadata={"source": "web", "url": url, "error": str(e)}
                ))
        return results

    def _validate_url(self, url: str) -> bool:
        """验证 URL 安全性，防止 SSRF 攻击"""
        from urllib.parse import urlparse
        import ipaddress

        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False

            # 获取主机名
            hostname = parsed.hostname
            if not hostname:
                return False

            # 检查是否为内网 IP
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                # 不是 IP 地址，检查域名
                if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"):
                    return False
                if hostname.endswith(".internal") or hostname.endswith(".local"):
                    return False

            return True
        except Exception:
            return False

    async def _fetch_page(self, url: str) -> WebPage:
        """获取网页内容"""
        # SSRF 防护
        if not self._validate_url(url):
            raise ValueError(f"URL not allowed: {url}")

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_length = len(response.content)
            if content_length > self.max_content_length:
                raise ValueError(f"Content too large: {content_length} bytes")

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else ""

            return WebPage(
                url=url,
                title=title.strip() if title else "",
                content=response.text,
                metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": content_length
                }
            )

    def _extract_content(self, html: str) -> str:
        """从 HTML 提取正文内容"""
        soup = BeautifulSoup(html, "html.parser")

        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            element.decompose()

        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find("div", class_=re.compile(r"content|main|article|body", re.I)) or
            soup.find("div", id=re.compile(r"content|main|article|body", re.I))
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """清理提取的文本"""
        # 先处理空行，再压缩空白
        text = re.sub(r"\n\s*\n", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    async def extract_links(self, url: str) -> List[str]:
        """提取网页中的链接"""
        try:
            page = await self._fetch_page(url)
            soup = BeautifulSoup(page.content, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("http://", "https://")):
                    links.append(href)
            return links
        except Exception as e:
            logger.error(f"Failed to extract links from {url}: {e}")
            return []

    async def crawl(
        self,
        start_url: str,
        max_pages: int = 10,
        allowed_domains: Optional[List[str]] = None
    ) -> List[WebPage]:
        """爬取网站"""
        visited = set()
        pages = []
        queue = [start_url]

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue

            if allowed_domains:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain not in allowed_domains:
                    continue

            try:
                page = await self._fetch_page(url)
                pages.append(page)
                visited.add(url)

                links = await self.extract_links(url)
                for link in links:
                    if link not in visited:
                        queue.append(link)

            except Exception as e:
                logger.warning(f"Failed to crawl {url}: {e}")
                visited.add(url)

        return pages
