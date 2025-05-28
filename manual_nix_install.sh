#!/bin/bash
# ブログ記事に基づいた手動Nixインストールスクリプト

echo "📦 Nix手動インストールを開始します..."

# 1. Nixボリュームの作成
echo "1. Nixボリュームを作成中..."
sudo diskutil apfs addVolume disk3 APFS 'Nix Store' -mountpoint /nix

# 2. synthetic.confの設定
echo "2. /etc/synthetic.confを設定中..."
echo 'nix' | sudo tee -a /etc/synthetic.conf

# 3. fstabの設定（オプション）
echo "3. /etc/fstabを設定中..."
echo 'LABEL=Nix\040Store /nix apfs rw,nobrowse' | sudo tee -a /etc/fstab

echo "✅ 準備が完了しました"
echo "⚠️  macOSを再起動してください"
echo ""
echo "再起動後、以下のコマンドでNixをインストールしてください："
echo "sh <(curl -L https://nixos.org/nix/install) --daemon"