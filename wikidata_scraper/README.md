# wikidata_scraper — Thu thập thực thể & mã/từ viết tắt từ Wikidata

Script Python (chỉ dùng thư viện chuẩn, không cần cài thêm) để truy vấn
**Wikidata Query Service (SPARQL)** và thu về các thực thể cùng các **mã /
từ viết tắt** của chúng (short name P1813, mã sân bay, mã quốc gia, mã niêm
yết, ký hiệu nguyên tố, mã ngôn ngữ, mã tiền tệ...).

---

## 1. Câu trả lời nhanh cho 4 câu hỏi quan trọng

### a) Truy vấn như thế nào?
Wikidata có một **SPARQL endpoint** tại:

```
https://query.wikidata.org/sparql
```

Bạn gửi **POST** với body dạng `application/x-www-form-urlencoded` chứa tham
số `query=<câu SPARQL>`. Câu truy vấn cơ bản để tìm thực thể + mã của chúng:

```sparql
# Tìm mọi thực thể là instance of (P31) một trong các class, hoặc thuộc
# subclass (P279*) của chúng, đồng thời có thuộc tính mã/từ viết tắt P1813.
SELECT ?item ?itemLabel ?abbr WHERE {
  VALUES ?class { wd:Q189533 }            # học vị (academic degree)
  ?item wdt:P31/wdt:P279* ?class .       # "là instance of OR subclass of class"
  ?item wdt:P1813 ?abbr .                # có thuộc tính "short name"
  SERVICE wikibase:label { bd:serviceParam wikibase:language "vi,en,multi". }
}
LIMIT 1000
```

Chạy trên web để thử dần: <https://query.wikidata.org/> (có autocomplete).

### b) Dữ liệu trả về định dạng gì?
Kèm header `Accept: application/sparql-results+json`, endpoint trả về **JSON
SPARQL**:

```json
{
  "head": { "vars": ["item", "itemLabel", "abbr"] },
  "results": { "bindings": [
    {
      "item": { "type": "uri",    "value": "http://www.wikidata.org/entity/Q2787220" },
      "itemLabel": { "type": "literal", "value": "Master of Education", "xml:lang": "en" },
      "abbr":     { "type": "literal", "value": "M.Ed." }
    }
  ]}
}
```

Mỗi hàng kết quả là một phần tử trong `results.bindings`; mỗi ô là một dict
`{"type": ..., "value": ...}` (kèm `"xml:lang"` cho chuỗi có ngôn ngữ).

### c) Giới hạn số request?
- **Giới hạn thời gian mỗi truy vấn: 60 giây** (endpoint hủy query quá lâu).
  → Đây là lý do script chia nhỏ và tách bỏ `wikibase:label` khỏi các query
  nặng.
- **Rate limit**: không có con số "tối đa request" chính thức, nhưng
  Wikimedia **yêu cầu** gửi chậm và đều. Quy tắc an toàn: **≤ 1–2 request/
  giây**, và **1 kết nối đồng thời**. Nếu bị **HTTP 429** thì phải chờ
  (backoff) trước khi thử lại.
- **User-Agent bắt buộc**: phải là chuỗi mô tả + contact. Nếu bỏ trống,
  Wikidata trả về **HTTP 403** (đây là lỗi thường gặp nhất khi viết client).

### d) Viết code thế nào?
→ Xem cấu trúc package bên dưới và thư mục `config.py` (nơi bạn thêm/bớt nhóm
và thuộc tính).

---

## 2. Cấu trúc thư mục

```
wikidata_scraper/
├── __init__.py      # API cấp cao collect_abbreviations(...)
├── config.py        # ★ NHÓM đối tượng + THUỘC TÍNH mã/từ viết tắt (sửa ở đây)
├── client.py        # HTTP client: User-Agent, rate-limit, retry, timeout
├── queries.py       # Sinh câu SPARQL, phân trang
├── collector.py     # Điều phối 2 giai đoạn + ghi JSONL/CSV/summary
└── run.py           # CLI entry point
run_wikidata_scraper.py   # ★ file gọi ở thư mục chính của repo
```

## 3. Cách chạy

Từ **thư mục chính của repo**:

```bash
# Chạy thử vài nhóm nhỏ trước khi chạy hết (kiểm tra nhanh):
python run_wikidata_scraper.py --groups airport,chemical_element,academic_degree --max-pages 3

# Chạy toàn bộ nhóm đã khai báo trong config:
python run_wikidata_scraper.py

# Tùy chọn thêm:
#   --groups name1,name2      chỉ chạy các nhóm này
#   --max-pages N            giới hạn số trang/nhóm (chạy nhanh để test)
#   --page-size N            dòng mỗi trang (mặc định 4000)
#   --sleep S                giây nghỉ giữa requests (mặc định 1.0)
#   --out DIR                thư mục ghi kết quả (mặc định data/)
```

Kết quả ghi vào `data/`:
- `wikidata_abbreviations.jsonl` — đầy đủ, 1 dòng 1 bản ghi JSON.
- `wikidata_abbreviations.tsv` — bảng TSV dễ mở bằng Excel/pandas.
- `wikidata_abbreviations_summary.txt` — tổng kết số lượng theo nhóm & thuộc tính.

## 4. Hai giai đoạn lấy dữ liệu (vì sao chia nhỏ?)

**Giai đoạn 1 — dữ liệu thô.** Với mỗi **(nhóm × 1 thuộc tính)**, gửi một
query *đơn giản, KHÔNG có* `wikibase:label`:

```sparql
SELECT ?item ?abbr WHERE {
  VALUES ?class { wd:Q1248784 }          # sân bay
  ?item wdt:P31/wdt:P279* ?class .
  ?item wdt:P238 ?abbr .                 # mã IATA
}
LIMIT 4000 OFFSET 0
```

Gom **một thuộc tính trong một query** (thay vì 9 thuộc tính/lần) và bỏ label
service khiến mỗi query nhỏ, nhanh → hạn chế timeout 60 giây.

**Giai đoạn 2 — lấy nhãn thực thể.** Gom toàn bộ QID thu được thành các lô
`VALUES ?item { wd:Q... }` nhỏ (2000 cái/lô) rồi gửi query nhãn riêng.

Kết quả này vừa đủ thông tin, vừa tránh được các lỗi timeout 403/504.

## 5. Khai báo nhóm & thuộc tính (`config.py`)

Bảng **`ENTITY_GROUPS`** — mỗi dòng là một NHÓM đối tượng với các **QID của
class** (lớp). Thêm nhóm mới chỉ cần thêm một tuple:

```python
("organization", "Tổ chức nói chung",
 "Lớp gốc organization (công ty, cơ quan, đoàn thể...).",
 ["Q43229"]),   # list class QID — có thể cho nhiều class cùng nhóm
```

Bảng **`ABBREVIATION_PROPERTIES`** — các **thuộc tính mã/từ viết tắt**:

| PID   | Ý nghĩa                                            | Ví dụ         |
|-------|----------------------------------------------------|---------------|
| P1813 | short name (tên viết tắt, dùng chung)              | M.Ed., UNESCO |
| P398  | abbreviation (từ viết tắt nói chung)               | ...           |
| P246  | element symbol (nguyên tố hóa học)                 | H, He, Li     |
| P238  | IATA airport code (sân bay)                        | SGN, HAN      |
| P2397 | ICAO airport code (sân bay)                        | VVTS          |
| P297  | ISO 3166-1 alpha-2 (quốc gia)                      | VN, US        |
| P395  | ISO 3166-1 numeric (quốc gia)                      | 704, 840      |
| P249  | ticker symbol / mã niêm yết (công ty đại chúng)    | AAPL, VNM     |
| P424  | Wikimedia language code (ngôn ngữ)                 | vi, en        |
| P2218 | ISO 4217 (đơn vị tiền tệ)                          | VND, USD      |
| P300  | ISO 3166-2 (đơn vị hành chính)                     | VN-HN         |

> Vì mỗi thuộc tính được áp cho *mọi* nhóm, một thực thể đồng thời ở nhiều nhóm
> sẽ có nhiều bản ghi; collector tự khử trùng lặp theo (item, thuộc tính, giá trị).

## 6. Những lưu ý quan trọng khi tự viết client

1. **Luôn gửi `User-Agent` chuẩn** — code client đã làm sẵn. Nếu tự viết, đừng
   quên; thiếu nó sẽ nhận **403**.
2. **`Accept: application/sparql-results+json`** để nhận JSON.
3. **Ngủ giữa các request** (script mặc định 1s) để dưới 1–2 req/s, tránh 429.
4. **Xử lý 429**: chờ theo `Retry-After` hoặc backoff (script dùng backoff 2^n).
5. **Giữ query gọn**: tránh `wikibase:label` trên query rộng; phân trang bằng
   `LIMIT`/`OFFSET`; một query phải xong trong 60 giây.
6. **Không spam**: muốn lấy toàn bộ thì chia nhỏ theo nhóm chạy từng lần (dùng
   đối số `--groups`), tránh chạy liên tục nhiều giờ không nghỉ.
7. Giá trị mã có thể là chuỗi (literal, VD `"SGN"`) hoặc URL của một thực thể
   khác; script chuẩn hoá URL về dạng `Q123` qua `value_to_text`.

## 7. Dùng trong code Python của bạn

```python
from wikidata_scraper import collect_abbreviations

records = collect_abbreviations(
    group_names=["airport", "chemical_element"],   # chạy riêng vài nhóm
    max_pages=2,                                   # giới hạn trang khi test
)
# records: list[dict] mỗi dict là 1 bản ghi (xem cấu trúc trong collector.py)
```