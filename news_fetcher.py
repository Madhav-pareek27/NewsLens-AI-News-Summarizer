"""Safely retrieve readable article text from a public HTML news URL."""
from __future__ import annotations

import html
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

MAX_DOWNLOAD_BYTES = 2_500_000
MAX_REDIRECTS = 5
USER_AGENT = "NewsSummarizerLearningProject/1.0 (article reader)"


def validate_public_url(url: str) -> None:
    """Reject local/private/non-HTTP destinations, including redirect targets.

    For internet-hosted production deployments, also enforce network-layer
    egress restrictions, since DNS can change between validation and request.
    """
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a complete public http:// or https:// news URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing usernames or passwords are not supported.")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(
        (".local", ".internal", ".localhost")
    ):
        raise ValueError("Local-network URLs are not allowed.")
    try:
        addresses = socket.getaddrinfo(
            hostname, parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except (socket.gaierror, OSError) as exc:
        raise ValueError("Could not resolve the website's hostname.") from exc
    if not addresses:
        raise ValueError("Could not resolve the website's hostname.")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0].split("%")[0])
        if not ip.is_global:
            raise ValueError("Private, local, and reserved IP addresses are not allowed.")


def reject_non_article_page(url: str) -> None:
    """Avoid treating news home pages, topic feeds and search pages as articles."""
    parsed = urlsplit(url.strip())
    hostname = (parsed.hostname or "").lower().rstrip(".")
    path = parsed.path.rstrip("/").lower()
    if hostname == "news.google.com" and (
        path in {"", "/home", "/topstories", "/foryou", "/following"}
        or path.startswith(("/topics", "/search", "/publications", "/sections"))
    ):
        raise ValueError(
            "This is a Google News feed, not an individual article. "
            "Open a specific news story and copy its article link, "
            "or paste the complete article text."
        )
    # A bare domain generally leads to a landing page containing navigation/headlines.
    if path == "" and hostname:
        raise ValueError(
            "This is a website homepage, not an article. "
            "Copy the URL of one complete news story or paste the article text."
        )


def fetch_article(url: str) -> tuple[str, str]:
    """Return (article text, final public URL) from a text/html resource."""
    target = url.strip()
    reject_non_article_page(target)
    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html"})
        for _ in range(MAX_REDIRECTS + 1):
            validate_public_url(target)
            reject_non_article_page(target)
            response = session.get(
                target, allow_redirects=False, stream=True, timeout=(6, 16)
            )
            try:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError("This URL redirected without a destination.")
                    target = urljoin(target, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if content_type and not (
                    "text/html" in content_type or "application/xhtml+xml" in content_type
                ):
                    raise ValueError("This URL is not an HTML article. Paste its text instead.")

                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_content(chunk_size=65536):
                    size += len(chunk)
                    if size > MAX_DOWNLOAD_BYTES:
                        raise ValueError("Article page is too large to fetch safely.")
                    chunks.append(chunk)
                page_html = b"".join(chunks).decode(
                    response.encoding or "utf-8", errors="replace"
                )
                break
            finally:
                response.close()
        else:
            raise ValueError("Too many redirects. Please paste the article text.")

    # Import only when a URL actually needs extraction.
    import trafilatura

    article = trafilatura.extract(
        page_html, url=target, include_comments=False,
        include_tables=False, favor_recall=False,
    )
    if not article or len(article.split()) < 20:
        soup = BeautifulSoup(page_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        # Avoid falling back to <main> or <body>: they often contain news feeds,
        # navigation cards and unrelated headlines rather than a specific story.
        candidate = soup.select_one(
            'article, [itemprop="articleBody"], .article-body, .story-body'
        )
        article = candidate.get_text(" ", strip=True) if candidate else ""

    if not article or len(article.strip()) < 40:
        raise ValueError(
            "No complete article could be extracted from this page. "
            "Use a direct article URL or paste the full text instead."
        )
    return article, target


def clean_news_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
