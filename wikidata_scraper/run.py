"""
Chạy thu thập từ CLI:
    python -m wikidata_scraper.run [--groups name1,name2] [--max-pages N]
                                    [--page-size N] [--sleep S] [--out DIR]

Hoặc gọi trực tiếp từ thư mục gốc (file run_wikidata_scraper.py).
"""

import argparse
import os

from .collector import collect_abbreviations
from .config import ENTITY_GROUPS, TEST_ENTITY_GROUPS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Thu thập mã/từ viết tắt từ Wikidata")
    # parser.add_argument(
    #     "--groups",
    #     help="Chỉ chạy các nhóm (phân tách bằng dấu phẩy). Danh sách hợp lệ: "
    #          + ", ".join(g[0] for g in ENTITY_GROUPS) + ".",
    # )
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Giới hạn số trang/query (None = không giới hạn).")
    parser.add_argument("--page-size", type=int, default=4000,
                        help="Số dòng mỗi trang (mặc định 4000, giữ nhỏ để tránh 60s).")
    parser.add_argument("--sleep", type=float, default=1.0,
                        help="Giây nghỉ giữa các request (mặc định 1.0).")
    parser.add_argument("--out", default="data",
                        help="Thư mục ghi file kết quả (mặc định data/).")

    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    group_names = [
        g[0] for g in ENTITY_GROUPS
    ]

    records = collect_abbreviations(
        output_jsonl=os.path.join(args.out, "wikidata_abbreviations.jsonl"),
        output_csv=os.path.join(args.out, "wikidata_abbreviations.tsv"),
        output_summary=os.path.join(args.out, "wikidata_abbreviations_summary.txt"),
        group_names=group_names,
        max_pages=args.max_pages,
        page_size=args.page_size,
        sleep_seconds=args.sleep,
    )
    print(f"\nXong. Ghi {len(records)} bản ghi vào {args.out}/")


if __name__ == "__main__":
    main()