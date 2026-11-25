"""
Entry point ở thư mục CHÍNH, gọi package thu thập Wikidata.

Chạy thử các nhóm NHỎ trước (sân bay, nguyên tố hóa học, học vị) để kiểm tra
rồi mở rộng:

    python run_wikidata_scraper.py --groups airport,chemical_element,academic_degree --max-pages 3

Chạy toàn bộ:

    python run_wikidata_scraper.py

Mọi tham số đều có thể đổi, xem `python run_wikidata_scraper.py --help`.
"""

import sys

sys.path.insert(0, ".")

from wikidata_scraper.run import main  # noqa: E402

if __name__ == "__main__":
    main()