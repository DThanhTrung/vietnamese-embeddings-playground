"""
HTTP client cho Wikidata SPARQL endpoint.

Chỉ dùng thư viện chuẩn (`urllib`) nên không cần cài thêm dependency.
Xử lý:
  - User-Agent đúng chuẩn (bắt buộc, nếu thiếu Wikidata trả 403).
  - Accept: application/sparql-results+json (định dạng trả về là JSON SPARQL).
  - Rate limiting: ngủ giữa các request để dưới 1-2 req/s.
  - Retry khi bị 429 (too many requests) / 5xx với exponential backoff.
  - Timeout của request (socket) để không treo mãi.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import SPARQL_ENDPOINT, USER_AGENT

# Định dạng kết quả JSON được SPARQL endpoint quy ước.
_ACCEPT = "application/sparql-results+json"
# Max 60 giây/truy vấn; đặt socket timeout thấp hơn để bắt lỗi sớm.
_SOCKET_TIMEOUT = 55.0
# Số lần thử lại tối đa cho mỗi request.
_MAX_RETRIES = 6


class WikidataSparqlError(RuntimeError):
    """Lỗi khi gọi SPARQL endpoint."""


class WikidataSparqlClient:
    """Client nhỏ gọn gửi SPARQL query và trả về binding JSON."""

    def __init__(
        self,
        endpoint: str = SPARQL_ENDPOINT,
        user_agent: str = USER_AGENT,
        sleep_seconds: float = 1.0,
        max_retries: int = _MAX_RETRIES,
    ):
        self.endpoint = endpoint
        self.user_agent = user_agent
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries

    # -- helper: lấy chuỗi giá trị trong binding kiểu SPARQL-JSON -----------
    @staticmethod
    def binding_value(binding: dict, key: str):
        """Trả về text value của một ô kết quả (binding) hoặc None."""
        node = binding.get(key)
        if not node:
            return None
        if "value" in node:
            return node["value"]
        return None

    @staticmethod
    def bindings(result: dict):
        """Trích mảng `results.bindings` từ JSON SPARQL, rỗng nếu không có."""
        try:
            return result["results"]["bindings"]
        except (KeyError, TypeError):
            return []

    # -- request chính ------------------------------------------------------
    def query(self, sparql: str, query_name: str = "query"):
        """
        Gửi một SPARQL SELECT và trả về tuple (bindings, head_vars).
        bindings: list[dict] mỗi phần tử là 1 hàng kết quả (key = tên biến).
        head_vars: list[str] tên các biến được SELECT.
        """
        data = urllib.parse.urlencode({"query": sparql}).encode("utf-8")
        headers = {
            "Accept": _ACCEPT,
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            time.sleep(self.sleep_seconds)  # rate-limit giữa các request
            req = urllib.request.Request(self.endpoint, data=data, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=_SOCKET_TIMEOUT) as resp:
                    payload = resp.read().decode("utf-8")
                    parsed = json.loads(payload)
                return parsed["results"]["bindings"], parsed.get("head", {}).get("vars", [])
            except urllib.error.HTTPError as exc:
                last_error = exc
                body = exc.read().decode("utf-8", errors="replace")[:500]
                if exc.code == 429:
                    wait = 2 ** attempt  # backoff cho rate-limit
                    print(f"[{query_name}] chờ rate-limit {wait}s (HTTP 429: {body})")
                    time.sleep(wait)
                    continue
                if exc.code == 400:
                    # Lỗi cú pháp SPARQL — không nên retry.
                    raise WikidataSparqlError(
                        f"SPARQL lỗi cú pháp (400) cho '{query_name}': {body}"
                    )
                print(f"[{query_name}] HTTP {exc.code} (attempt {attempt}), retry...")
            except urllib.error.URLError as exc:
                last_error = exc
                print(f"[{query_name}] URLError (attempt {attempt}): {exc.reason}")
            except (json.JSONDecodeError, TimeoutError) as exc:
                last_error = exc
                print(f"[{query_name}] decode/timeout lỗi (attempt {attempt}): {exc}")

        raise WikidataSparqlError(
            f"Thất bại sau {self.max_retries} lần thử cho '{query_name}': {last_error}"
        )