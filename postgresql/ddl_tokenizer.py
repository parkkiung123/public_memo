"""
ddl_tokenizer.py
----------------
CREATE TABLE DDL のテーブル名・カラム名をトークン化（匿名化）し、
逆変換（復元）もできるモジュール。

変換例:
    orders          -> TBL_001
    orders.order_id -> COL_001
    ...

CHECK 制約内のカラム参照・REFERENCES の参照先など、
カラム「定義」以外の箇所は置換しない。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# 型定義
# ---------------------------------------------------------------------------
@dataclass
class TokenMapping:
    """テーブル名・カラム名のトークンマッピング。"""

    table_map: dict[str, str] = field(default_factory=dict)   # table_name -> TBL_XXX
    column_map: dict[str, str] = field(default_factory=dict)  # table.col  -> COL_XXX

    # ------------------------------------------------------------------
    # 既存メソッド
    # ------------------------------------------------------------------

    def reverse(self) -> "TokenMapping":
        """逆変換用マッピングを返す（トークン -> 元の名前）。"""
        return TokenMapping(
            table_map={v: k for k, v in self.table_map.items()},
            column_map={v: k for k, v in self.column_map.items()},
        )

    def as_flat_dict(self) -> dict[str, str]:
        """table_map と column_map を結合した辞書を返す。"""
        return {**self.table_map, **self.column_map}

    # ------------------------------------------------------------------
    # JSON シリアライズ
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """辞書形式に変換する。"""
        return {
            "table_map": self.table_map,
            "column_map": self.column_map,
        }

    def to_json(self, indent: int = 2) -> str:
        """JSON 文字列に変換する。

        Args:
            indent: インデント幅（デフォルト: 2）

        Returns:
            JSON 文字列

        Example:
            >>> mapping.to_json()
            '''
            {
              "table_map": {"orders": "TBL_001"},
              "column_map": {"orders.order_id": "COL_001", ...}
            }
            '''
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save_json(self, path: str | Path, indent: int = 2) -> None:
        """JSON ファイルに保存する。

        Args:
            path:   保存先ファイルパス
            indent: インデント幅（デフォルト: 2）
        """
        Path(path).write_text(self.to_json(indent), encoding="utf-8")

    # ------------------------------------------------------------------
    # JSON デシリアライズ
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "TokenMapping":
        """辞書から TokenMapping を復元する。

        Args:
            data: to_dict() で生成した辞書

        Returns:
            TokenMapping
        """
        return cls(
            table_map=dict(data.get("table_map", {})),
            column_map=dict(data.get("column_map", {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TokenMapping":
        """JSON 文字列から TokenMapping を復元する。

        Args:
            json_str: to_json() で生成した JSON 文字列

        Returns:
            TokenMapping
        """
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load_json(cls, path: str | Path) -> "TokenMapping":
        """JSON ファイルから TokenMapping を復元する。

        Args:
            path: save_json() で保存したファイルパス

        Returns:
            TokenMapping
        """
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# パース補助
# ---------------------------------------------------------------------------
_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\S+)\s*\(",
    re.IGNORECASE,
)

# 制約キーワードで始まる行はカラム定義ではない
_CONSTRAINT_KEYWORDS = re.compile(
    r"^\s*(PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT)\b",
    re.IGNORECASE,
)

# カラム定義行: インデント + 識別子 + 空白
_COLUMN_LINE_RE = re.compile(r"^(\s+)(\w+)\s", re.UNICODE)


def _extract_table_name(ddl: str) -> str:
    m = _CREATE_TABLE_RE.search(ddl)
    if not m:
        raise ValueError("CREATE TABLE 文が見つかりません")
    return m.group(1).strip('"').strip("`")


def _extract_column_names(ddl: str) -> list[str]:
    """DDL のカラム定義行からカラム名の一覧を取得する。"""
    start = ddl.find("(")
    if start == -1:
        raise ValueError("開き括弧が見つかりません")

    depth = 0
    end = -1
    for i, ch in enumerate(ddl[start:], start):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        raise ValueError("括弧が閉じていません")

    body = ddl[start + 1 : end]
    columns: list[str] = []
    for line in body.splitlines():
        if _CONSTRAINT_KEYWORDS.match(line):
            continue
        m = _COLUMN_LINE_RE.match(line)
        if m:
            columns.append(m.group(2))
    return columns


# ---------------------------------------------------------------------------
# マッピング生成
# ---------------------------------------------------------------------------
def build_mapping(
    ddl: str,
    table_prefix: str = "TBL",
    column_prefix: str = "COL",
    table_start: int = 1,
    column_start: int = 1,
) -> TokenMapping:
    """
    DDL を解析してトークンマッピングを生成する。

    Args:
        ddl:           CREATE TABLE 文
        table_prefix:  テーブルトークンのプレフィックス（デフォルト: "TBL"）
        column_prefix: カラムトークンのプレフィックス（デフォルト: "COL"）
        table_start:   テーブル連番の開始値（デフォルト: 1）
        column_start:  カラム連番の開始値（デフォルト: 1）

    Returns:
        TokenMapping
    """
    table_name = _extract_table_name(ddl)
    short_name = table_name.split(".")[-1]  # スキーマ修飾を除いた名前
    columns = _extract_column_names(ddl)

    table_map = {table_name: f"{table_prefix}_{table_start:03d}"}
    column_map = {
        f"{short_name}.{col}": f"{column_prefix}_{column_start + i:03d}"
        for i, col in enumerate(columns)
    }

    return TokenMapping(table_map=table_map, column_map=column_map)


# ---------------------------------------------------------------------------
# 変換エンジン
# ---------------------------------------------------------------------------
def _col_token_dict(mapping: TokenMapping) -> dict[str, str]:
    """
    column_map からカラム名だけをキーにした辞書を作る。
    順変換: キーは "table.col" 形式なので "." 以降を取り出す。
    逆変換: キーはトークン (COL_XXX) 形式でドットがないのでそのまま使う。
    """
    result = {}
    for k, v in mapping.column_map.items():
        short_key = k.split(".", 1)[-1]  # ドットがない場合はそのまま
        short_val = v.split(".", 1)[-1]  # 逆変換時: 'orders.order_id' -> 'order_id'
        result[short_key] = short_val
    return result


def _apply_mapping(ddl: str, mapping: TokenMapping) -> str:
    """
    マッピングに従って DDL のテーブル名とカラム名を置換する。

    置換対象:
      1. CREATE TABLE <table_name> の table_name
      2. カラム定義行の先頭カラム名（CHECK・REFERENCES 内は変更しない）
    """
    result = ddl

    # 1. テーブル名（CREATE TABLE の直後のみ）
    for original, token in mapping.table_map.items():
        result = re.sub(
            r"(CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?)" + re.escape(original),
            r"\g<1>" + token,
            result,
            flags=re.IGNORECASE,
        )

    # 2. カラム名（各行の先頭のみ）
    col_tokens = _col_token_dict(mapping)

    lines = result.splitlines(keepends=True)
    new_lines: list[str] = []
    for line in lines:
        if not _CONSTRAINT_KEYWORDS.match(line):
            m = _COLUMN_LINE_RE.match(line)
            if m:
                col_name = m.group(2)
                if col_name in col_tokens:
                    line = re.sub(
                        r"^(\s+)" + re.escape(col_name) + r"(\s)",
                        r"\g<1>" + col_tokens[col_name] + r"\g<2>",
                        line,
                        count=1,
                    )
        new_lines.append(line)

    return "".join(new_lines)


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------
def tokenize(ddl: str, mapping: TokenMapping | None = None) -> tuple[str, TokenMapping]:
    """
    DDL のテーブル名・カラム名をトークンに置換する。

    Args:
        ddl:     元の CREATE TABLE 文
        mapping: 既存のマッピングを使う場合に指定（None なら自動生成）

    Returns:
        (tokenized_ddl, mapping) のタプル
    """
    if mapping is None:
        mapping = build_mapping(ddl)
    return _apply_mapping(ddl, mapping), mapping


def detokenize(tokenized_ddl: str, mapping: TokenMapping) -> str:
    """
    トークン化された DDL を元のテーブル名・カラム名に戻す。

    Args:
        tokenized_ddl: tokenize() で生成したトークン化済み DDL
        mapping:       tokenize() が返した TokenMapping

    Returns:
        元の DDL
    """
    return _apply_mapping(tokenized_ddl, mapping.reverse())

# ---------------------------------------------------------------------------
# 汎用テキスト逆変換
# ---------------------------------------------------------------------------
def restore_tokens(text: str, mapping: TokenMapping) -> str:
    """
    任意のテキスト（SELECT 文など）に含まれるトークンを元の名前に戻す。

    mapping.json の値（トークン）-> キー（元の名前）に単純全文置換する。
    column_map のキーは "table.col" 形式なので、戻す際はカラム名部分のみ使用。

    長いトークンを先に置換することで部分一致の誤爆を防ぐ。

    Args:
        text:    変換対象のテキスト（SQL、説明文など何でも可）
        mapping: tokenize() が返した TokenMapping（または load_json で読んだもの）

    Returns:
        トークンを元の名前に置き換えたテキスト
    """
    # トークン -> 元の名前 の辞書を作る
    # column_map: "orders.order_id" -> "주문아이디"  の逆なので
    #             "주문아이디" -> "order_id"  （テーブル名部分は除く）
    replacements: dict[str, str] = {}

    for original, token in mapping.table_map.items():
        replacements[token] = original  # 주문테이블 -> orders

    for original, token in mapping.column_map.items():
        col_name = original.split(".", 1)[-1]   # orders.order_id -> order_id
        replacements[token] = col_name          # 주문아이디 -> order_id

    # 長いトークンを先に処理（部分一致誤爆防止）
    result = text
    for token, original in sorted(replacements.items(), key=lambda x: -len(x[0])):
        result = result.replace(token, original)

    return result

# ---------------------------------------------------------------------------
# デモ
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    SAMPLE_DDL = text

    tokenized_ddl, mapping = tokenize(SAMPLE_DDL)

    # トークン化 & 保存
    #mapping.save_json("mapping.json")

    # mapping.jsonをカスタマイズ
    # 別のプロセスで復元
    mapping = TokenMapping.load_json("mapping.json")
    tokenized_ddl = _apply_mapping(SAMPLE_DDL, mapping)

    print("=== マッピング ===")
    for k, v in mapping.as_flat_dict().items():
        print(f"  {k!r}: {v!r}")

    print("\n=== トークン化後 DDL ===")
    print(tokenized_ddl)

    restored_ddl = detokenize(tokenized_ddl, mapping)
    print("\n=== 逆変換後 DDL ===")
    print(restored_ddl)

    SAMPLE_DDL = """\
SELECT *
    FROM 주문테이블
    WHERE 스테이터스 = 'paid';
    """
    result = restore_tokens(SAMPLE_DDL, mapping)
    print(result)

    print()
    print("=== 元の DDL と一致:", SAMPLE_DDL == restored_ddl, "===")
