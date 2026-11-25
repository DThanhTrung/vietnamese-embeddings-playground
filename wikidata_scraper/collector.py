"""
Điều phối việc thu thập theo 2 giai đoạn (tránh timeout 60s):

  GĐ1 - lấy dữ liệu thô trong (nhóm × thuộc tính), lặp từng thuộc tính một
        (query nhỏ, nhanh).
  GĐ2 - gom toàn bộ QID thu được, lấy nhãn thực thể theo lô VALUES nhỏ.

Mỗi bản ghi cuối mang đủ: nhóm đối tượng (tên + mô tả + class QID), thực thể
(QID + nhãn), thuộc tính mã/từ viết tắt (PID + tên + mô tả), và giá trị mã.
"""

import csv
import json
import time
from collections import defaultdict
from typing import Optional

from .client import WikidataSparqlClient, WikidataSparqlError
from .config import (
    ABBREVIATION_PROPERTIES,
    DEFAULT_MAX_PAGES,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SLEEP_SECONDS,
    ENTITY_GROUPS,
)

from .queries import (
    iter_abbr_pages, 
    normalize_wikidata_url, 
    prop_meta, 
    value_to_text, 
    build_label_query
)


_PROP_META = prop_meta()
_LABEL_BATCH = 2000  # số QID mỗi query lấy nhãn (giữ nhỏ để không timeout)


class Collector:
    """Chạy thu thập cho một tập nhóm. Có thể tái sử dụng."""

    def __init__(
        self,
        client: Optional[WikidataSparqlClient] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_pages: Optional[int] = DEFAULT_MAX_PAGES,
        label_batch: int = _LABEL_BATCH,
    ):
        self.client = client or WikidataSparqlClient()
        self.page_size = page_size
        self.max_pages = max_pages
        self.label_batch = label_batch

    # -- GĐ1: dữ liệu thô cho một nhóm -------------------------------------
    def _collect_group_raw(self, group_name, group_desc, group_classes):
        records = {}
        props = [meta[0] for meta in ABBREVIATION_PROPERTIES]
        # props = ["P1813"]

        for prop in props :
            first = True
            for query, offset in iter_abbr_pages(
                group_classes, prop, self.page_size, self.max_pages
            ) :
                bindings, _ = self.client.query(query, query_name=f"{group_name}.{prop}.p{offset}")
                local = 0
                for b in bindings:
                    item = normalize_wikidata_url(self.client.binding_value(b, "item") or "")
                    abbr = value_to_text(self.client.binding_value(b, "abbr") or "")
                    if not item or not abbr:
                        continue
                    key = (item, prop, abbr)
                    if key in records:
                        continue
                    records[key] = {
                        "group": group_name,
                        "group_description": group_desc,
                        "class_qids": ",".join(group_classes),
                        "item": item,
                        "item_label": "",
                        "abbr_property": prop,
                        "abbr_property_label": _PROP_META.get(prop, (prop, ""))[0],
                        "abbr_property_description": _PROP_META.get(prop, ("", ""))[1],
                        "abbreviation": abbr,
                    }
                    local += 1
                print(
                    f"    [{group_name} | {prop}] page {offset // self.page_size}: "
                    f"+{local} ({len(records)} lũy kế)"
                )
                if len(bindings) < self.page_size:
                    break
                if first:  # chỉ sleep cực ngắn giữa các trang của cùng thuộc tính
                    first = False
        return list(records.values())

    # -- GĐ2: lấy nhãn thực thể theo lô VALUES nhỏ ---------------------------
    def _label_pass(self, records):
        items = sorted({r["item"] for r in records})
        label_map = {}
        for batch_no, query in enumerate(build_label_query(items, self.label_batch)):
            bindings, _ = self.client.query(query, query_name=f"labels.b{batch_no}")
            for b in bindings:
                item = normalize_wikidata_url(self.client.binding_value(b, "item") or "")
                lbl = self.client.binding_value(b, "itemLabel")
                if item and lbl and item not in label_map:
                    label_map[item] = lbl
            print(
                f"    [labels] batch {batch_no + 1}: "
                f"đã có {len(label_map)}/{len(records)} nhãn"
            )

        for r in records:
            r["item_label"] = label_map.get(r["item"], "")

    # -- vòng ngoài ---------------------------------------------------------
    def collect(self, group_names: Optional[list] = None) -> list:
        groups = ENTITY_GROUPS
        if group_names is not None:
            names = set(group_names)
            groups = [g for g in ENTITY_GROUPS if g[0] in names]

        raw = []
        for group_name, label, desc, classes in groups:
            print(f"\n=== Nhóm: {label} ({group_name}) — class {classes} ===")
            try:
                raw += self._collect_group_raw(group_name, desc, classes)
            except WikidataSparqlError as exc:
                print(f"!! Bỏ qua nhóm {group_name}: {exc}")
                continue

        raw = self._dedupe(raw)
        print(f"\n=== GĐ2: lấy nhãn thực thể cho {len(raw)} bản ghi (={len(set(r['item'] for r in raw))} thực thể) ===")
        self._label_pass(raw)
        return raw

    @staticmethod
    def _dedupe(records):
        seen, keep = set(), []
        for r in records:
            key = (r["item"], r["abbr_property"], r["abbreviation"])
            if key in seen:
                continue
            seen.add(key)
            keep.append(r)
        return keep

# --------------------------------------------------------------------------- #
# Ghi ra file
# --------------------------------------------------------------------------- #
def write_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(records, path):
    headers = ["group", "group_description", "class_qids", "item", "item_label",
               "abbr_property", "abbr_property_label", "abbr_property_description",
               "abbreviation"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in headers})


def write_summary(records, path):
    by_group = defaultdict(set)
    by_group_prop = defaultdict(set)
    by_prop = defaultdict(set)
    for r in records:
        by_group[r["group"]].add((r["item"], r["abbr_property"]))
        by_group_prop[(r["group"], r["abbr_property"])].add(r["item"])
        by_prop[r["abbr_property"]].add(r["item"])

    lines = [
        "== TỔNG KẾT THU THẬP WIKIDATA ==",
        f"Tổng bản ghi (item x thuộc tính x giá trị): {len(records)}",
        "",
        "== Theo thuộc tính ==",
    ]
    for pid in sorted(by_prop):
        lines.append(f"  {pid} ({_PROP_META.get(pid, ('', ''))[0]}): {len(by_prop[pid])} thực thể")
    lines.append("")
    lines.append("== Theo nhóm ==")
    for g in sorted(by_group):
        lines.append(f"  {g}: {len(by_group[g])} cặp (item, thuộc tính)")
    lines.append("")
    lines.append("== Theo (nhóm, thuộc tính) ==")
    for (g, p) in sorted(by_group_prop):
        lines.append(f"  {g:20s} | {p:7s} | {len(by_group_prop[(g, p)]):6d} thực thể")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def collect_abbreviations(
    output_jsonl="data/wikidata_abbreviations.jsonl",
    output_csv="data/wikidata_abbreviations.tsv",
    output_summary="data/wikidata_abbreviations_summary.txt",
    group_names=None,
    max_pages=DEFAULT_MAX_PAGES,
    page_size=DEFAULT_PAGE_SIZE,
    sleep_seconds=DEFAULT_SLEEP_SECONDS,
):
    """API cấp cao: thu thập + ghi 3 file. Trả về danh sách bản ghi."""
    client = WikidataSparqlClient(sleep_seconds=sleep_seconds)
    collector = Collector(client=client, page_size=page_size, max_pages=max_pages)
    records = collector.collect(group_names=group_names)

    write_jsonl(records, output_jsonl)
    write_csv(records, output_csv)
    write_summary(records, output_summary)
    return records