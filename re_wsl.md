✅ 解決策：wsl --export + wsl --import による再圧縮（正式手順）
💡 これは ext4.vhdx を物理的に再圧縮する唯一の方法です。
🔧 手順（例：Ubuntu）

以下は「Ubuntu」という WSL ディストリビューションを圧縮し直す流れです。

① 一時的なバックアップ先を作成
mkdir D:\WSLBackup

② ディストリのエクスポート（.tar 化）
wsl --export Ubuntu D:\WSLBackup\ubuntu_backup.tar

③ 元の Ubuntu をアンレジスター（削除）

⚠️ これで元の環境は消えるので、問題ないことを確認してから実行してください！

wsl --unregister Ubuntu

④ 再インポート（再構築）
wsl --import Ubuntu D:\WSLNew D:\WSLBackup\ubuntu_backup.tar


これで、新しい ext4.vhdx が圧縮された状態で作成されます。

📌 補足

再インポート後の Ubuntu は初回起動に時間がかかる場合があります

D:\WSLNew は新しい保存先（空き容量が十分ある場所にする）

再インポート後も ~ やファイル構成は同じです