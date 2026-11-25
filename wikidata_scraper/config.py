"""
Định nghĩa các NHÓM ĐỐI TƯỢNG và các THUỘC TÍNH MÃ/TỪ VIẾT TẮT trên Wikidata.

Mỗi nhóm là một tập các class (lớp đối tượng), được tham chiếu bằng QID.
Wikidata cho phép truy vấn "instance of + subclass of*" qua mẫu:
    ?item wdt:P31/wdt:P279* wd:<QID-của-class>
nghĩa là "lấy mọi thực thể là (trực tiếp hoặc gián tiếp qua lớp con) một
thể hiện của class đó", ví dụ một trường đại học là instance of `university`.

Mỗi hàng config giải thích QID thuộc nhóm gì, dễ theo dõi/dễ thêm bớt.
"""

# ---------------------------------------------------------------------------
# CÁC NHÓM ĐỐI TƯỢNG
# Mỗi phần tử: (Tên hiển thị bằng tiếng Việt, mô tả ngắn, [list các QID class]).
# Muốn thêm nhóm mới chỉ cần thêm một tuple; script tự sinh SPARQL.
# ---------------------------------------------------------------------------
TEST_ENTITY_GROUPS = [
    ("university",
    "Trường đại học",
    "Q3918 = university.",
    ["Q3918"])
]

ENTITY_GROUPS = [
    # Nhóm "Tổ chức nói chung". Q43229 = organization (lớp cha của nhiều tổ
    # chức: công ty, cơ quan, đoàn thể...). Lọc theo class này sẽ bắt được
    # rất nhiều thực thể có mã/tên viết tắt.
    ("organization",
     "Tổ chức nói chung",
     "Lớp gốc organization (gồm công ty, cơ quan, đoàn thể, viện, hiệp hội...).",
     ["Q43229"]),

    ("government_agency",
     "Cơ quan chính phủ",
     "Q327333 = government agency (bộ, tổng cục, cơ quan nhà nước).",
     ["Q327333"]),

    ("ngo",
     "Tổ chức phi chính phủ",
     "Q79913 = non-governmental organization (NGO).",
     ["Q79913"]),

    ("currency",
     "Đơn vị tiền tệ",
     "Q8142 = currency (đồng tiền tệ, VD: VND, USD...).",
     ["Q8142"]),

    (
        "stock_exchange",
        "Sàn giao dịch",
        "Q11691 = stock_exchange (NYSE, NASDAQ, HOSE)",
        ["Q11691"],
    ),

    ("file_format",
     "Định dạng tệp",
     "Q235557 = file format (jpeg, pdf, mp4...).",
     ["Q235557"]),

    ("disease",
     "Bệnh lý",
     "Q12136 = disease (bệnh, rối loạn; mã thường dùng ICD/OMM/HGNC...).",
     ["Q12136"]),

    ("academic_degree",
     "Học vị",
     "Q189533 = academic degree (cử nhân, thạc sĩ, tiến sĩ...; mã viết tắt tên gọi).",
     ["Q189533"]),

    ("university",
     "Trường đại học",
     "Q3918 = university.",
     ["Q3918"]),

    ("airport",
     "Sân bay",
     "Q1248784 = airport (dùng mã IATA P238, ICAO P239).",
     ["Q1248784"]),

    ("chemical_element",
     "Nguyên tố hóa học",
     "Q11344 = chemical element (mã nguyên tố P246: H, He, O...).",
     ["Q11344"]),

    ("sovereign_state",
     "Quốc gia có chủ quyền",
     "Q6256 = sovereign state (dùng mã quốc gia P297 ISO 3166-1 alpha-2).",
     ["Q6256"]),

    ("company",
     "Công ty nói chung",
     "Q783794 = company.",
     ["Q783794"]),

    ("public_company",
     "Công ty niêm yết (đại chúng)",
     "Q891723 = public company / listed company (dùng mã niêm yết P249).",
     ["Q891723"]),

    ("language",
     "Ngôn ngữ",
     "Q34770 = language (dùng mã ngôn ngữ P424: vi, en, fr...).",
     ["Q34770"]),
]

# ---------------------------------------------------------------------------
# CÁC THUỘC TÍNH MÃ / TỪ VIẾT TẮT
# Mỗi phần tử: (QID thuộc tính, Tên tiếng Việt, mô tả).
# ---------------------------------------------------------------------------
ABBREVIATION_PROPERTIES = [
    # P1813: tên viết tắt / short name (thuộc tính "từ viết tắt" phổ quát nhất)
    ("P1813", "Tên viết tắt", "short name — dùng chung cho mọi nhóm đối tượng."),
    # P398: abbreviation (property generic "abbreviation")
    ("P398", "Từ viết tắt", "abbreviation — thuộc tính viết tắt nói chung."),
    # P246: element symbol (nguyên tố hóa học)
    ("P246", "Ký hiệu nguyên tố", "element symbol — VD: H, He, Li."),
    # P238: IATA airport code (sân bay)
    ("P238", "Mã sân bay IATA", "IATA airport code — VD: SGN, HAN."),
    # P2397: ICAO airport code (sân bay)
    ("P239", "Mã sân bay ICAO", "ICAO airport code — VD: VVTS, WSSS."),
    # P297: ISO 3166-1 alpha-2 (quốc gia)
    ("P297", "Mã quốc gia ISO 2 ký tự", "ISO 3166-1 alpha-2 — VD: VN, US."),
    # P395: ISO 3166-1 numeric (quốc gia)
    ("P395", "Mã quốc gia ISO số", "ISO 3166-1 numeric — VD: VN=704, US=840."),
    # P249: mã niêm yết sàn chứng khoán (công ty đại chúng)
    ("P249", "Mã niêm yết chứng khoán", "ticker symbol / mã giao dịch sàn chứng khoán."),
    # P424: Wikimedia language code (ngôn ngữ)
    ("P424", "Mã ngôn ngữ", "Wikimedia language code — VD: vi, en."),
    # P2218: ISO 4217 (mã đơn vị tiền tệ)
    ("P2218", "Mã ISO 4217", "ISO 4217 — VD: VND, USD, EUR."),
    # P300: ISO 3166-2 (mã đơn vị hành chính cấp 2)
    ("P300", "Mã ISO 3166-2", "ISO 3166-2 — VD: VN-HN, VN-SGN."),
    # P528: Định danh của sàn giao dịch chứng khoán
    ("P528", "Mã sàn giao dịch chứng khoán", "VD: SWX, UN, US")
]

# ---------------------------------------------------------------------------
# Cài đặt giao thức request (xem file README).
# ---------------------------------------------------------------------------
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# User-Agent do Wikidata YÊU CẦU: phải mô tả contact để tránh bị chặn 403.
# Nên đặt địa chỉ email/URL thật của bạn.
USER_AGENT = "vietnamese-embeddings-playground/0.1 (contact: 24022472@vnu.edu.vn)"

# Khoảng nghỉ giữa 2 request (giây) — đảm bảo không quá 1-2 request/giây.
DEFAULT_SLEEP_SECONDS = 1.0

# Kích thước mỗi trang kết quả cho mỗi (nhóm) query — giữ nhỏ để tránh
# endpoint trả về lỗi quá thời gian 60 giây.
DEFAULT_PAGE_SIZE = 4000

# Số trang tối đa mỗi nhóm (bảo vệ chạy quá lâu). None = không giới hạn.
DEFAULT_MAX_PAGES = None