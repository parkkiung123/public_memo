要件を整理すると、こうですね：

* **systemd サービス**として起動
* サービス内で

  * `docker exec` を使って **コンテナに user ユーザーで入る**
  * **user の `.bashrc が実行された状態`**
  * その状態で **`xxxx.sh` を実行**

ポイントは
👉 **非対話シェルでは `.bashrc` は自動では読まれない**
👉 `bash -lc` を使うのが定番解決策

---

## ① 基本方針（重要）

```bash
docker exec -u user <container> bash -lc "/path/to/xxxx.sh"
```

* `-l` : login shell（.bash_profile → .bashrc が読まれる）
* `-c` : コマンド実行
* `bash -lc` にすることで **.bashrc が確実に有効**

---

## ② 実行用スクリプト（ホスト側）

例：
`/usr/local/bin/run_xxxx_in_container.sh`

```bash
#!/bin/bash
set -e

CONTAINER_NAME=my_container
CONTAINER_USER=user
SCRIPT_PATH=/home/user/xxxx.sh

docker exec \
  -u ${CONTAINER_USER} \
  ${CONTAINER_NAME} \
  bash -lc "${SCRIPT_PATH}"
```

```bash
chmod +x /usr/local/bin/run_xxxx_in_container.sh
```

---

## ③ systemd サービスファイル

### `/etc/systemd/system/run-xxxx.service`

```ini
[Unit]
Description=Run xxxx.sh inside docker container as user with bashrc
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/run_xxxx_in_container.sh
RemainAfterExit=yes

# 必要なら
# User=root

[Install]
WantedBy=multi-user.target
```

---

## ④ systemd 反映・起動

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

sudo systemctl start run-xxxx.service
sudo systemctl status run-xxxx.service
```

自動起動したい場合：

```bash
sudo systemctl enable run-xxxx.service
```

---

## ⑤ よくある落とし穴（重要）

### ❌ `.bashrc` が読まれない

```bash
bash -c xxxx.sh   # ←ダメ
```

### ✅ 正解

```bash
bash -lc xxxx.sh
```

---

### ❌ `docker exec -it` を使う

* systemd では **TTY がない**
* `-it` は **使わない**

---

## ⑥ `.bashrc` が本当に読まれているか確認

`.bashrc` に一時的に追加：

```bash
echo "bashrc loaded" > /tmp/bashrc_loaded.log
```

実行後：

```bash
docker exec my_container cat /tmp/bashrc_loaded.log
```

---

## ⑦ まとめ（最小構成）

```text
systemd
  ↓
host script
  ↓
docker exec -u user
  ↓
bash -lc xxxx.sh
  ↓
.bashrc 有効状態で実行
```

---

必要なら次も出せます👇

* コンテナが起動していなければ待つ版
* `Environment=` を使った systemd 設定
* `timer`（cron 代替）
* docker-compose 環境対応

どこまでやりたいですか？
