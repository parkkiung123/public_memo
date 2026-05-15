# Linux / Shell コマンドチートシート

## grep（テキスト検索）

```bash
grep "text" file
```

* `-i`：大文字小文字を区別しない
* `-n`：行番号を表示
* `-v`：一致しない行を表示（除外）
* `-r`：ディレクトリを再帰検索
* `-l`：ファイル名だけ表示
* `-c`：一致件数のみ表示
* `-E`：拡張正規表現

## journalctl（systemdログ）

```bash
journalctl
```

* `-f`：リアルタイム追従（tail -f）
* `-u xxx.service`：サービス指定
* `-n 100`：最新100行表示

## ファイル検索・テキスト処理

### find（ファイル検索）

```bash
find /path -name "*.log"
```

### sed（置換・編集）

```bash
sed 's/old/new/g' file
sed -i 's/old/new/g' file   # 直接編集
```

### awk（列処理）

```bash
awk '{print $1}' file
```

### cut（列抽出）

```bash
cut -d',' -f1 file
```

### uniq（重複整理）

```bash
sort file | uniq
```

※uniqは連続した重複のみ対象

### xargs（引数化して実行）

```bash
cat list | xargs rm
```

## 閲覧・監視系

* `less -N file`：行番号付き表示
* `watch cmd`：定期実行
* `wc`：行数・単語数・バイト数

## システム系コマンド

* `export`：環境変数設定
* `which`：コマンドの場所
* `df`：ディスク全体使用量
* `du`：ディレクトリ単位容量
* `env`：環境変数一覧

## Shell基礎構文

* 変数：`$var`
* 条件分岐：

```bash
if [ condition ]; then
fi
```

* ループ：

```bash
for i in {1..10}; do
    echo "$i 秒..."
    sleep 1  # 1秒待機するコマンド
done
for ((i=1; i<=10; i++)); do
    echo "$i 秒..."
    sleep 1
done
i=1
while [[ $i -le 10 ]]; do
    echo "$i 秒..."
    sleep 1
    # カウンタを1増やす (忘れると無限ループになるので注意！)
    i=$((i + 1))
done
echo "10秒経過しました。"
```

* 引数：

```bash
$1  # 第1引数
```

* パイプ：

```bash
cmd1 | cmd2
```

* コマンド置換：

```bash
$(cmd)
```

* 算術式展開：

```bash
$((10+11))
```

## リダイレクト

```bash
>   # 上書き
>>  # 追記
<   # 入力
2>  # エラー出力
```

## set（シェル設定）

デフォルトではOFF：

| 設定              | 意味         |
| --------------- | ---------- |
| set -e          | エラーで停止しない  |
| set -u          | 未定義変数OK    |
| set -o pipefail | パイプ途中失敗を無視 |

## デフォルト値（引数）

```bash
LIMIT="${1:-100}"
```

意味：

* `$1` があればそれを使う
* なければ `100`

## source
変数,共通関数を現在のプロセス内で読み込む
```
#!/bin/bash

# 設定ファイルを読み込む（source または .）
source ./config.env

# 読み込んだ変数をそのまま使える
echo "接続先DB: $DB_NAME"
psql -d $DB_NAME -U $DB_USER -c "SELECT 1;"
```
