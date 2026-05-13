\encoding UTF8

-- PostgreSQL learning sample data
-- Run after 01_create_tables.sql:
--   psql -U postgres -d your_database -f 02_insert_sample_data.sql

INSERT INTO customers (customer_name, email, prefecture, registered_at, is_active) VALUES
    ('田中 太郎', 'taro.tanaka@example.com', '東京都', '2026-01-10', TRUE),
    ('佐藤 花子', 'hanako.sato@example.com', '神奈川県', '2026-01-18', TRUE),
    ('鈴木 一郎', 'ichiro.suzuki@example.com', '大阪府', '2026-02-03', TRUE),
    ('高橋 美咲', 'misaki.takahashi@example.com', '愛知県', '2026-02-20', FALSE),
    ('伊藤 健', 'ken.ito@example.com', '北海道', '2026-03-05', TRUE),
    ('渡辺 玲奈', 'reina.watanabe@example.com', '福岡県', '2026-03-22', TRUE);

INSERT INTO categories (category_name) VALUES
    ('書籍'),
    ('文房具'),
    ('食品'),
    ('家電');

INSERT INTO products (product_name, category_id, price, stock_quantity, discontinued) VALUES
    ('PostgreSQL入門', 1, 3200, 20, FALSE),
    ('SQL練習ドリル', 1, 2400, 15, FALSE),
    ('ノート A5', 2, 280, 100, FALSE),
    ('ボールペン 黒', 2, 120, 200, FALSE),
    ('ドリップコーヒー', 3, 980, 50, FALSE),
    ('チョコレート', 3, 450, 0, FALSE),
    ('USBキーボード', 4, 4200, 8, FALSE),
    ('旧型マウス', 4, 1500, 3, TRUE);

INSERT INTO orders (customer_id, ordered_at, status, shipping_fee) VALUES
    (1, '2026-04-01 10:15:00', 'paid', 500),
    (1, '2026-04-15 19:40:00', 'shipped', 0),
    (2, '2026-04-03 12:05:00', 'shipped', 500),
    (3, '2026-04-05 09:30:00', 'cancelled', 0),
    (3, '2026-04-21 14:20:00', 'paid', 500),
    (5, '2026-04-25 16:45:00', 'pending', 500),
    (6, '2026-05-02 11:10:00', 'paid', 0);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 3200),
    (1, 3, 3, 280),
    (1, 4, 2, 120),
    (2, 5, 2, 980),
    (2, 6, 1, 450),
    (3, 2, 1, 2400),
    (3, 4, 5, 120),
    (4, 7, 1, 4200),
    (5, 1, 1, 3200),
    (5, 5, 1, 980),
    (6, 3, 10, 280),
    (6, 4, 10, 120),
    (7, 2, 1, 2400),
    (7, 7, 1, 4200);
