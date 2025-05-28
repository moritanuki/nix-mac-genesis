#!/bin/bash
# Nix関連の設定を完全にクリーンアップするスクリプト

echo "🧹 Nixのクリーンアップを開始します..."

# 1. Nixデーモンを停止
echo "1. Nixデーモンを停止中..."
sudo launchctl unload /Library/LaunchDaemons/org.nixos.nix-daemon.plist 2>/dev/null || true
sudo rm -f /Library/LaunchDaemons/org.nixos.nix-daemon.plist

# 2. Nixボリュームをアンマウント
echo "2. Nixボリュームをアンマウント中..."
sudo diskutil unmount force /nix 2>/dev/null || true

# 3. synthetic.confを削除
echo "3. synthetic.confのnixエントリを削除中..."
if [ -f /etc/synthetic.conf ]; then
    sudo sed -i '' '/^nix/d' /etc/synthetic.conf
    # ファイルが空になったら削除
    if [ ! -s /etc/synthetic.conf ]; then
        sudo rm -f /etc/synthetic.conf
    fi
fi

# 4. /nixディレクトリを削除
echo "4. /nixディレクトリを削除中..."
sudo rm -rf /nix

# 5. Nixユーザーとグループを削除
echo "5. Nixビルドユーザーを削除中..."
for i in $(seq 1 32); do
    sudo dscl . -delete /Users/_nixbld$i 2>/dev/null || true
done
sudo dscl . -delete /Groups/nixbld 2>/dev/null || true

# 6. Nix設定ファイルを削除
echo "6. Nix設定ファイルを削除中..."
sudo rm -rf /etc/nix
sudo rm -f /etc/profile.d/nix.sh
sudo rm -f /etc/profile.d/nix-daemon.sh

# 7. シェル設定のバックアップを復元
echo "7. シェル設定を復元中..."
if [ -f /etc/bashrc.backup-before-nix ]; then
    sudo mv /etc/bashrc.backup-before-nix /etc/bashrc
fi
if [ -f /etc/zshrc.backup-before-nix ]; then
    sudo mv /etc/zshrc.backup-before-nix /etc/zshrc
fi

# 8. Nixボリュームを削除
echo "8. Nixボリュームを削除中..."
if diskutil list | grep -q "Nix Store"; then
    # ボリュームのディスク識別子を取得
    NIX_VOLUME=$(diskutil list | grep "Nix Store" | awk '{print $NF}')
    if [ -n "$NIX_VOLUME" ]; then
        echo "   Nixボリューム $NIX_VOLUME を削除します..."
        sudo diskutil apfs deleteVolume $NIX_VOLUME 2>/dev/null || true
    fi
fi

# 9. ユーザーディレクトリのNix関連ファイルを削除
echo "9. ユーザーディレクトリのNix関連ファイルを削除中..."
rm -rf ~/.nix-profile
rm -rf ~/.nix-defexpr
rm -rf ~/.nix-channels
rm -rf ~/.local/state/nix
rm -rf ~/.cache/nix

echo "✅ Nixのクリーンアップが完了しました！"
echo ""
echo "⚠️  重要: macOSを再起動することを強く推奨します"
echo "   再起動後、以下のコマンドでNixを再インストールできます："
echo "   python3 bootstrap.py"