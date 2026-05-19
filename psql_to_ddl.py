"""
psql_to_ddl.py
--------------
PostgreSQL の \\d <table> 出力を CREATE TABLE 文に変換するモジュール。

Usage:
    from psql_to_ddl import convert

    sql = convert(psql_output)
    print(sql)
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 型名の正規化マッピング
# ---------------------------------------------------------------------------
_TYPE_ALIASES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bcharacter varying\b", re.I), "VARCHAR"),
    (re.compile(r"\bcharacter\b", re.I),         "CHAR"),
    (re.compile(r"\btimestamp without time zone\b", re.I), "TIMESTAMP"),
    (re.compile(r"\btimestamp with time zone\b",    re.I), "TIMESTAMPTZ"),
    (re.compile(r"\btime without time zone\b", re.I), "TIME"),
    (re.compile(r"\btime with time zone\b",    re.I), "TIMETZ"),
    (re.compile(r"\bdouble precision\b",       re.I), "DOUBLE PRECISION"),
]


def _normalize_type(raw: str) -> str:
    for pattern, replacement in _TYPE_ALIASES:
        raw = pattern.sub(replacement, raw)
    return raw.strip()


# ---------------------------------------------------------------------------
# データクラス
# ---------------------------------------------------------------------------
@dataclass
class ColumnDef:
    name: str
    col_type: str
    not_null: bool = False
    is_identity: bool = False
    default: str | None = None


@dataclass
class ParsedTable:
    table_name: str
    columns: list[ColumnDef] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    # col_name -> IN リスト (例: ["'pending'", "'paid'"])
    col_check_in: dict[str, list[str]] = field(default_factory=dict)
    # カラムに紐付かないテーブルレベルの CHECK 式
    table_checks: list[str] = field(default_factory=list)
    # col_name -> "referenced_table(col)" 文字列
    foreign_keys: dict[str, str] = field(default_factory=dict)
    unique_groups: list[list[str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# パース処理
# ---------------------------------------------------------------------------
_SECTION_PATTERNS: dict[str, re.Pattern] = {
    "indexes":     re.compile(r"^Indexes:\s*$"),
    "check":       re.compile(r"^Check constraints:\s*$"),
    "fk":          re.compile(r"^Foreign-key constraints:\s*$"),
    "unique":      re.compile(r"^Unique constraints:\s*$"),
    "referenced":  re.compile(r"^Referenced by:\s*$"),
    "triggers":    re.compile(r"^Triggers:\s*$"),
    "rules":       re.compile(r"^Rules:\s*$"),
}


def _detect_section(line: str) -> str | None:
    for name, pat in _SECTION_PATTERNS.items():
        if pat.match(line):
            return name
    return None


def _parse_check_expr(expr: str) -> dict:
    """
    CHECK 式を解析し、単純な IN リストか生の式かを返す。

    Returns:
        {"col": str, "in_list": [str, ...]}  または  {"raw": str}
    """
    # ::type および ::type[] キャストを除去
    expr = re.sub(r"::[a-z ]+(?:\[\])?", "", expr).strip()

    # col = ANY (ARRAY['a', 'b', ...])
    m = re.match(
        r"^(\w+)\s*=\s*ANY\s*\(\s*ARRAY\[(.+?)\]\s*\)$", expr, re.I
    )
    if m:
        col = m.group(1)
        raw_vals = m.group(2)
        vals = [
            f"'{v.strip().strip(chr(39))}'"
            for v in raw_vals.split(",")
        ]
        return {"col": col, "in_list": vals}

    return {"raw": expr}


def _parse_columns(lines: list[str], data_start: int, data_end: int) -> list[ColumnDef]:
    cols: list[ColumnDef] = []
    for line in lines[data_start:data_end]:
        if not line.strip():
            break
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not parts[0]:
            continue

        name      = parts[0]
        col_type  = parts[1]
        nullable  = parts[3] if len(parts) > 3 else ""
        default   = parts[4] if len(parts) > 4 else ""

        is_not_null = "not null" in nullable.lower()
        is_identity = "generated" in default.lower() and "identity" in default.lower()

        cols.append(ColumnDef(
            name=name,
            col_type=_normalize_type(col_type),
            not_null=is_not_null,
            is_identity=is_identity,
            default=None if (not default or is_identity) else default.strip(),
        ))
    return cols


def _find_column_region(lines: list[str]) -> tuple[int, int]:
    """
    ヘッダー行とセパレーター行を探し、データ開始行と終了行を返す。
    """
    header_idx = sep_idx = -1
    for i, line in enumerate(lines):
        if header_idx == -1 and re.match(r"^\s+Column\s+\|", line):
            header_idx = i
        elif header_idx != -1 and sep_idx == -1 and re.match(r"^[-\s|+]+$", line):
            sep_idx = i
            break

    if sep_idx == -1:
        raise ValueError("カラム定義のセパレーター行が見つかりません")

    data_start = sep_idx + 1
    data_end = len(lines)
    for i in range(data_start, len(lines)):
        if re.match(r"^[A-Z][a-z].*:\s*$", lines[i].strip()):
            data_end = i
            break

    return data_start, data_end


def parse(psql_output: str) -> ParsedTable:
    """\\d 出力テキストを ParsedTable に変換する。"""
    lines = psql_output.splitlines()

    # テーブル名
    table_match = re.search(r'Table\s+"([^"]+)"', psql_output)
    if not table_match:
        raise ValueError('Table "..." の行が見つかりません')
    table_name = table_match.group(1)

    result = ParsedTable(table_name=table_name)

    # カラム定義
    data_start, data_end = _find_column_region(lines)
    result.columns = _parse_columns(lines, data_start, data_end)

    if not result.columns:
        raise ValueError("カラム定義が解析できませんでした")

    # セクションのパース
    section = ""
    for line in lines[data_end:]:
        stripped = line.strip()
        detected = _detect_section(stripped)
        if detected:
            section = detected
            continue

        if not stripped:
            continue

        if section == "indexes":
            # PRIMARY KEY
            m = re.search(r'"[^"]*"\s+PRIMARY KEY,\s+\w+\s+\(([^)]+)\)', stripped, re.I)
            if m:
                result.primary_keys = [k.strip() for k in m.group(1).split(",")]

        elif section == "check":
            m = re.search(r'"[^"]+"\s+CHECK\s+\((.+)\)\s*$', stripped, re.I)
            if m:
                parsed = _parse_check_expr(m.group(1))
                if "col" in parsed:
                    result.col_check_in[parsed["col"]] = parsed["in_list"]
                else:
                    result.table_checks.append(parsed["raw"])

        elif section == "fk":
            m = re.search(
                r'"([^"]+)"\s+FOREIGN KEY\s+\(([^)]+)\)\s+REFERENCES\s+(\S+)\s*(?:\(([^)]+)\))?',
                stripped, re.I,
            )
            if m:
                col      = m.group(2).strip()
                ref_tbl  = m.group(3)
                ref_col  = m.group(4).strip() if m.group(4) else None
                ref_str  = f"{ref_tbl}({ref_col})" if ref_col else ref_tbl
                result.foreign_keys[col] = ref_str

        elif section == "unique":
            m = re.search(r'"[^"]+"\s+UNIQUE CONSTRAINT,\s+\w+\s+\(([^)]+)\)', stripped, re.I)
            if m:
                result.unique_groups.append([k.strip() for k in m.group(1).split(",")])

    return result


# ---------------------------------------------------------------------------
# SQL 生成
# ---------------------------------------------------------------------------
def _build_column_clause(col: ColumnDef, result: ParsedTable) -> str:
    pk_single = len(result.primary_keys) == 1

    parts = [col.name, col.col_type]

    if col.is_identity:
        parts.append("GENERATED ALWAYS AS IDENTITY PRIMARY KEY")
    else:
        if pk_single and col.name in result.primary_keys:
            parts.append("PRIMARY KEY")
        if col.not_null:
            parts.append("NOT NULL")
        if col.default:
            parts.append(f"DEFAULT {col.default}")
        if col.name in result.col_check_in:
            vals = ", ".join(result.col_check_in[col.name])
            parts.append(f"CHECK ({col.name} IN ({vals}))")
        if col.name in result.foreign_keys:
            parts.append(f"REFERENCES {result.foreign_keys[col.name]}")

    return " ".join(parts)


def generate_sql(result: ParsedTable) -> str:
    """ParsedTable から CREATE TABLE 文を生成する。"""
    clauses: list[str] = []

    for col in result.columns:
        clauses.append(_build_column_clause(col, result))

    if len(result.primary_keys) > 1:
        pk_cols = ", ".join(result.primary_keys)
        clauses.append(f"PRIMARY KEY ({pk_cols})")

    for group in result.unique_groups:
        clauses.append(f"UNIQUE ({', '.join(group)})")

    for ch in result.table_checks:
        clauses.append(f"CHECK ({ch})")

    indent = "    "
    body = f",\n{indent}".join(clauses)
    return f"CREATE TABLE {result.table_name} (\n{indent}{body}\n);"


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------
def convert(psql_output: str) -> str:
    """
    PostgreSQL の \\d <table> 出力を CREATE TABLE 文に変換する。

    Args:
        psql_output: psql の \\d コマンド出力テキスト

    Returns:
        CREATE TABLE SQL 文字列

    Raises:
        ValueError: 解析に失敗した場合
    """
    result = parse(psql_output)
    return generate_sql(result)


# ---------------------------------------------------------------------------
# CLI / デモ
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    print(convert(text))
