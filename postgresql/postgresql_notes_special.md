# PostgreSQL実務向けメモ

PostgreSQLで現場作業をするときに役立つ機能のまとめです。

## EXPLAIN (ANALYZE, BUFFERS)

Queryの性能分析に使います。

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 10;
```

主に見るポイント:

- `Execution Time`: 実際の実行時間
- `Seq Scan`: テーブルを全件読む
- `Index Scan`: インデックスを使って読む
- `Rows Removed by Filter`: 条件に合わず除外された行数
- `Buffers: shared hit`: メモリ上のキャッシュから読んだ量
- `Buffers: shared read`: ディスクから読んだ量

`EXPLAIN ANALYZE` は実際にSQLを実行します。`UPDATE` / `DELETE` / `INSERT` で試すときは、必要に応じて `BEGIN` と `ROLLBACK` を使います。

```sql
BEGIN;

EXPLAIN ANALYZE
UPDATE products
SET stock_quantity = stock_quantity - 1
WHERE product_id = 1;

ROLLBACK;
```

## RETURNING

登録・更新・削除した結果を、その場で返せます。

自動採番されたIDをすぐ取得したいときに便利です。

```sql
INSERT INTO customers (customer_name, email, prefecture)
VALUES ('山田 太郎', 'yamada@example.com', '東京都')
RETURNING customer_id;
```

複数列を返すこともできます。

```sql
INSERT INTO customers (customer_name, email, prefecture)
VALUES ('佐藤 花子', 'sato@example.com', '神奈川県')
RETURNING customer_id, customer_name, registered_at;
```

## ON CONFLICT

重複したときの処理を書けます。

いわゆるUPSERTです。

```text
なければ追加
あれば更新
```

```sql
INSERT INTO customers (customer_name, email, prefecture)
VALUES ('山田 太郎', 'yamada@example.com', '東京都')
ON CONFLICT (email)
DO UPDATE SET customer_name = EXCLUDED.customer_name;
```

`EXCLUDED` は、今回INSERTしようとした値を表します。

重複したら何もしない場合:

```sql
INSERT INTO customers (customer_name, email, prefecture)
VALUES ('山田 太郎', 'yamada@example.com', '東京都')
ON CONFLICT (email)
DO NOTHING;
```

## ILIKE

大文字小文字を区別しない `LIKE` です。

```sql
SELECT *
FROM customers
WHERE email ILIKE '%EXAMPLE.COM';
```

`example.com`、`EXAMPLE.COM`、`Example.Com` のような違いを無視して検索できます。

## JSONB

JSONを保存・検索できます。

`JSONB` はJSONをバイナリ形式で保存する型です。検索やインデックス利用に向いています。

```sql
CREATE TABLE events (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payload JSONB NOT NULL
);
```

```sql
INSERT INTO events (payload)
VALUES ('{"type": "login", "user_id": 1, "success": true}');
```

JSON内の値をテキストとして取り出す例:

```sql
SELECT *
FROM events
WHERE payload->>'type' = 'login';
```

よく使う演算子:

- `->`: JSONとして取り出す
- `->>`: テキストとして取り出す

## ARRAY

1列に複数値を持たせられます。

```sql
CREATE TABLE articles (
    article_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL,
    tags TEXT[] NOT NULL
);
```

```sql
INSERT INTO articles (title, tags)
VALUES ('PostgreSQL入門', ARRAY['sql', 'postgresql', 'database']);
```

配列に特定の値が含まれるか調べる例:

```sql
SELECT *
FROM articles
WHERE 'postgresql' = ANY(tags);
```

注意点として、現場では配列よりも別テーブルに分けたほうが良い場合も多いです。

タグを厳密に管理したい場合は、中間テーブルを使う設計も検討します。

## WITH

複雑なSQLを読みやすく分割できます。

名前付きサブクエリのようなものです。CTEとも呼びます。

```sql
WITH paid_orders AS (
    SELECT *
    FROM orders
    WHERE status = 'paid'
)
SELECT *
FROM paid_orders;
```

顧客別売上のように、先に注文単位で集計してから顧客単位で集計したい場合に便利です。

```sql
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.quantity * oi.unit_price) + o.shipping_fee AS order_total
    FROM orders AS o
    JOIN order_items AS oi
      ON o.order_id = oi.order_id
    WHERE o.status <> 'cancelled'
    GROUP BY o.order_id, o.customer_id, o.shipping_fee
)
SELECT
    c.customer_id,
    c.customer_name,
    COALESCE(SUM(ot.order_total), 0) AS sales_total
FROM customers AS c
LEFT JOIN order_totals AS ot
  ON c.customer_id = ot.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY sales_total DESC;
```

## ウィンドウ関数

集計しつつ、行を潰さずに順位・累計・前後比較などを出せます。

普通の `GROUP BY` は行をまとめますが、ウィンドウ関数は元の行を残したまま計算結果を追加できます。

```sql
SELECT
    customer_id,
    ordered_at,
    SUM(shipping_fee) OVER (
        PARTITION BY customer_id
        ORDER BY ordered_at
    ) AS running_shipping_fee
FROM orders;
```

結果イメージ:

```text
customer_id | ordered_at          | running_shipping_fee
------------+---------------------+---------------------
1           | 2026-04-01 10:15:00 | 500.00
1           | 2026-04-15 19:40:00 | 500.00
2           | 2026-04-03 12:05:00 | 500.00
3           | 2026-04-05 09:30:00 | 0.00
3           | 2026-04-21 14:20:00 | 500.00
5           | 2026-04-25 16:45:00 | 500.00
6           | 2026-05-02 11:10:00 | 0.00
```

よく使うウィンドウ関数:

- `ROW_NUMBER()`: 連番
- `RANK()`: 順位。同順位があると次の順位が飛ぶ
- `DENSE_RANK()`: 順位。同順位があっても次の順位が飛ばない
- `LAG()`: 前の行の値
- `LEAD()`: 次の行の値
- `SUM() OVER`: 累計
- `COUNT() OVER`: 件数を行ごとに表示

例: 顧客ごとの注文順に番号を振る

```sql
SELECT
    customer_id,
    ordered_at,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY ordered_at
    ) AS order_number
FROM orders;
```

例: 前回注文日を出す

```sql
SELECT
    customer_id,
    ordered_at,
    LAG(ordered_at) OVER (
        PARTITION BY customer_id
        ORDER BY ordered_at
    ) AS previous_ordered_at
FROM orders;
```

## generate_series

日付一覧や連番をSQL内で作れます。

連番を作る例:

```sql
SELECT generate_series(1, 10);
```

日付一覧を作る例:

```sql
SELECT generate_series(
    DATE '2026-05-01',
    DATE '2026-05-07',
    INTERVAL '1 day'
);
```

売上がない日も含めた日別集計で便利です。

```sql
WITH dates AS (
    SELECT generate_series(
        DATE '2026-04-01',
        DATE '2026-04-30',
        INTERVAL '1 day'
    )::date AS order_date
),
daily_sales AS (
    SELECT
        DATE(o.ordered_at) AS order_date,
        SUM(oi.quantity * oi.unit_price + 0) AS sales_amount
    FROM orders AS o
    JOIN order_items AS oi
      ON o.order_id = oi.order_id
    WHERE o.status <> 'cancelled'
    GROUP BY DATE(o.ordered_at)
)
SELECT
    d.order_date,
    COALESCE(ds.sales_amount, 0) AS sales_amount
FROM dates AS d
LEFT JOIN daily_sales AS ds
  ON d.order_date = ds.order_date
ORDER BY d.order_date;
```

## ざっくり使いどころ

| 機能 | 使いどころ |
|---|---|
| `EXPLAIN (ANALYZE, BUFFERS)` | SQLの性能分析 |
| `RETURNING` | 登録・更新した結果をすぐ取得 |
| `ON CONFLICT` | 重複時に更新、または何もしない |
| `ILIKE` | 大文字小文字を無視して検索 |
| `JSONB` | 柔軟なJSONデータを保存・検索 |
| `ARRAY` | 1列に複数値を持たせる |
| `WITH` | 複雑なSQLを読みやすく分割 |
| ウィンドウ関数 | ランキング、累計、前後比較 |
| `generate_series` | 日付一覧や連番を作る |

## csvで高速INSERT
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\copy target_table FROM 'data_from_java.csv' WITH CSV"
