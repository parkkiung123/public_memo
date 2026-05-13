\encoding UTF8

-- PostgreSQL practice queries
-- Run after loading sample data, or copy one query at a time into psql.

-- 1. 全顧客を登録日順に表示
SELECT
    customer_id,
    customer_name,
    prefecture,
    registered_at
FROM customers
ORDER BY registered_at;

-- 2. 在庫がある販売中の商品だけ表示
SELECT
    product_name,
    price,
    stock_quantity
FROM products
WHERE stock_quantity > 0
  AND discontinued = FALSE
ORDER BY price DESC;

-- 3. 商品とカテゴリをJOINして表示
SELECT
    p.product_name,
    c.category_name,
    p.price
FROM products AS p
JOIN categories AS c
  ON p.category_id = c.category_id
ORDER BY c.category_name, p.product_name;

-- 4. 注文ごとの商品小計を計算
SELECT
    oi.order_id,
    SUM(oi.quantity * oi.unit_price) AS item_total
FROM order_items AS oi
GROUP BY oi.order_id
ORDER BY oi.order_id;

-- 5. 注文ごとの合計金額を送料込みで計算
SELECT
    o.order_id,
    c.customer_name,
    o.status,
    SUM(oi.quantity * oi.unit_price) + o.shipping_fee AS order_total
FROM orders AS o
JOIN customers AS c
  ON o.customer_id = c.customer_id
JOIN order_items AS oi
  ON o.order_id = oi.order_id
GROUP BY o.order_id, c.customer_name, o.status, o.shipping_fee
ORDER BY o.order_id;

-- 6. 顧客ごとの注文回数と購入合計を集計
SELECT
    c.customer_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    COALESCE(SUM(oi.quantity * oi.unit_price + 0), 0) AS total_items_amount
FROM customers AS c
LEFT JOIN orders AS o
  ON c.customer_id = o.customer_id
 AND o.status <> 'cancelled'
LEFT JOIN order_items AS oi
  ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_items_amount DESC;

-- 7. カテゴリ別の売上を集計
SELECT
    cat.category_name,
    SUM(oi.quantity * oi.unit_price) AS sales_amount
FROM categories AS cat
JOIN products AS p
  ON cat.category_id = p.category_id
JOIN order_items AS oi
  ON p.product_id = oi.product_id
JOIN orders AS o
  ON oi.order_id = o.order_id
WHERE o.status <> 'cancelled'
GROUP BY cat.category_id, cat.category_name
ORDER BY sales_amount DESC;

-- 8. まだ注文していない顧客を探す
SELECT
    c.customer_name,
    c.email
FROM customers AS c
LEFT JOIN orders AS o
  ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;

-- 9. 2026年4月の注文を日別に集計
SELECT
    DATE(ordered_at) AS order_date,
    COUNT(*) AS order_count
FROM orders
WHERE ordered_at >= '2026-04-01'
  AND ordered_at < '2026-05-01'
GROUP BY DATE(ordered_at)
ORDER BY order_date;

-- 10. 商品価格を税込表示にする例
SELECT
    product_name,
    price AS price_without_tax,
    ROUND(price * 1.10, 0) AS price_with_tax
FROM products
ORDER BY product_id;

-- 11. 顧客別の売上を送料込みで集計
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.quantity * oi.unit_price) AS item_total,
        o.shipping_fee,
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
    COUNT(ot.order_id) AS order_count,
    COALESCE(SUM(ot.item_total), 0) AS item_total,
    COALESCE(SUM(ot.shipping_fee), 0) AS shipping_total,
    COALESCE(SUM(ot.order_total), 0) AS sales_total_with_shipping
FROM customers AS c
LEFT JOIN order_totals AS ot
  ON c.customer_id = ot.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY sales_total_with_shipping DESC;
