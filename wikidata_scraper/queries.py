"""
Xây dựng câu SPARQL cho từng nhóm đối tượng.

Hai giai đoạn để TRÁNH quá tải / timeout 60 giây của endpoint:

  (1) Lấy dữ liệu thô: mỗi (nhóm × 1 thuộc tính) là một query đơn giản,
      KHÔNG dùng wine SERVICE wikibase:label (đây là phần nặng gây timeout).
      Kết quả là cặp (item QID, giá trị mã viết tắt).

  (2) Lấy nhãn thực thể: gom toàn bộ QID thu thập được thành các lô VALUES
      nhỏ rồi gửi query nhãn riêng (nhanh, ít tốn tài nguyên).

Mẫu query giai đoạn (1), cho class [Q1,...] và thuộc tính Pp:

    SELECT ?item ?abbr WHERE {
      VALUES ?class { wd:Q1 wd:Q2 ... }
      ?item wdt:P31/wdt:P279* ?class .
      ?item wdt:Pp ?abbr .
    }
    LIMIT X OFFSET Y
"""

from typing import Iterator, List, Tuple


def build_abbr_query(
    group_classes: List[str],
    abbr_property: str,   # VD: "P1813"
    page_size: int,
    offset: int,
) -> str:
    """Query giai đoạn (1): lấy (item, giá trị mã) cho một thuộc tính đơn."""
    values_cls = " ".join(f"wd:{c}" for c in group_classes)
    return (
    f"""
        SELECT ?item ?abbr WHERE {{
            VALUES ?class {{ {values_cls} }}
            ?item wdt:P31/wdt:P279* ?class .
            ?item wdt:{abbr_property} ?abbr .

            # FILTER(LANG(?abbr) = "en")
        }}
        LIMIT {page_size} OFFSET {offset}
    """
    )

def build_label_query(items: List[str], chunk: int = 2000) -> List[str]:
    """Query giai đoạn (2): lấy nhãn cho một lô QID (chunk tối đa `chunk` cái)."""
    queries = []
    for i in range(0, len(items), chunk):
        batch = items[i:i + chunk]
        values = " ".join(f"wd:{q}" for q in batch)
        queries.append(
        f"""
            SELECT ?item ?itemLabel WHERE {{
                VALUES ?item {{ {values} }}
                SERVICE wikibase:label {{
                    bd:serviceParam wikibase:language "vi,en".
                }}
            }}
        """
        )
    return queries


def iter_abbr_pages(
    group_classes: List[str],
    abbr_property: str,
    page_size: int,
    max_pages=None,
) -> Iterator[Tuple[str, int]]:
    """Sinh (query, offset) các trang của một (nhóm × thuộc tính)."""
    offset = 0
    while True:
        if max_pages is not None and offset // page_size >= max_pages:
            break
        yield build_abbr_query(group_classes, abbr_property, page_size, offset), offset
        offset += page_size


def normalize_wikidata_url(value: str) -> str:
    """Đổi URL Wikidata (https://www.wikidata.org/wiki/Q...) về dạng 'Q123'."""
    if value.startswith("http"):
        return value.rstrip("/").rsplit("/", 1)[-1]
    return value


def value_to_text(value: str) -> str:
    """Trả về chuỗi giá trị: nếu là URL thì lấy phần cuối, nếu literal thì giữ."""
    return normalize_wikidata_url(value)


# Bản đồ PID -> (tên Việt, mô tả) để ghi chú thích mỗi thuộc tính.
def prop_meta() -> dict:
    from .config import ABBREVIATION_PROPERTIES
    return {pid: (name, desc) for pid, name, desc in ABBREVIATION_PROPERTIES}