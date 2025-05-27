"""
セキュリティ関連の機能を管理するモジュール
"""

import subprocess
import os
import logging
from pathlib import Path
import base64
import json
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityManager:
    """セキュリティ関連の機能を管理するクラス"""
    
    def __init__(self, logger):
        self.logger = logger
        self.keychain_name = "nix-mac-genesis"
        self.backup_dir = Path.home() / '.nix-mac-genesis-backup'
        
    def setup_keychain(self):
        """macOSキーチェーンの設定"""
        self.logger.info("キーチェーン設定を構成中...")
        
        # SSH鍵のパスフレーズをキーチェーンに追加
        ssh_key_path = Path.home() / '.ssh' / 'id_ed25519'
        if ssh_key_path.exists():
            try:
                # ssh-addでキーチェーンに追加
                subprocess.run(
                    ['ssh-add', '--apple-use-keychain', str(ssh_key_path)],
                    check=True
                )
                self.logger.info("✅ SSH鍵をキーチェーンに追加しました")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"SSH鍵のキーチェーン追加に失敗: {e}")
                
    def store_secret(self, service, account, secret):
        """キーチェーンにシークレットを保存"""
        try:
            # 既存のエントリを削除
            subprocess.run(
                [
                    'security', 'delete-generic-password',
                    '-s', service,
                    '-a', account
                ],
                capture_output=True
            )
        except:
            # 既存エントリがない場合は無視
            pass
            
        # 新しいエントリを追加
        try:
            subprocess.run(
                [
                    'security', 'add-generic-password',
                    '-s', service,
                    '-a', account,
                    '-w', secret,
                    '-T', ''  # すべてのアプリからアクセス可能
                ],
                check=True
            )
            self.logger.info(f"✅ シークレットを保存: {service}/{account}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"シークレット保存エラー: {e}")
            raise
            
    def retrieve_secret(self, service, account):
        """キーチェーンからシークレットを取得"""
        try:
            result = subprocess.run(
                [
                    'security', 'find-generic-password',
                    '-s', service,
                    '-a', account,
                    '-w'
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            self.logger.warning(f"シークレットが見つかりません: {service}/{account}")
            return None
            
    def backup_keys(self, passphrase=None):
        """SSH/GPG鍵の暗号化バックアップ"""
        self.logger.info("鍵のバックアップを作成中...")
        
        # バックアップディレクトリの作成
        self.backup_dir.mkdir(mode=0o700, exist_ok=True)
        
        # パスフレーズの取得
        if not passphrase:
            passphrase = getpass.getpass("バックアップ用パスフレーズ: ")
            if not passphrase:
                raise ValueError("パスフレーズが必要です")
                
        # 暗号化キーの生成
        key = self._derive_key(passphrase)
        fernet = Fernet(key)
        
        # バックアップするファイル
        files_to_backup = [
            Path.home() / '.ssh' / 'id_ed25519',
            Path.home() / '.ssh' / 'id_ed25519.pub',
            Path.home() / '.ssh' / 'config',
        ]
        
        # GPG鍵のエクスポート
        gpg_backup_data = self._export_gpg_keys()
        if gpg_backup_data:
            gpg_backup_path = self.backup_dir / 'gpg-keys.asc'
            encrypted_gpg = fernet.encrypt(gpg_backup_data.encode())
            gpg_backup_path.write_bytes(encrypted_gpg)
            self.logger.info(f"✅ GPG鍵をバックアップ: {gpg_backup_path}")
            
        # ファイルのバックアップ
        for file_path in files_to_backup:
            if file_path.exists():
                self.logger.info(f"バックアップ中: {file_path}")
                
                # ファイル内容を読み込み
                content = file_path.read_bytes()
                
                # 暗号化
                encrypted_content = fernet.encrypt(content)
                
                # バックアップファイルとして保存
                backup_path = self.backup_dir / f"{file_path.name}.encrypted"
                backup_path.write_bytes(encrypted_content)
                
                # 権限設定
                os.chmod(backup_path, 0o600)
                
        # バックアップ情報の保存
        backup_info = {
            'timestamp': subprocess.run(
                ['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'],
                capture_output=True,
                text=True
            ).stdout.strip(),
            'files': [str(f) for f in files_to_backup if f.exists()],
            'gpg_included': bool(gpg_backup_data)
        }
        
        info_path = self.backup_dir / 'backup-info.json'
        info_path.write_text(json.dumps(backup_info, indent=2))
        
        self.logger.info(f"✅ バックアップが完了しました: {self.backup_dir}")
        
    def restore_keys(self, backup_dir=None, passphrase=None):
        """バックアップから鍵を復元"""
        if not backup_dir:
            backup_dir = self.backup_dir
        else:
            backup_dir = Path(backup_dir)
            
        if not backup_dir.exists():
            raise ValueError(f"バックアップディレクトリが見つかりません: {backup_dir}")
            
        self.logger.info(f"バックアップから復元中: {backup_dir}")
        
        # パスフレーズの取得
        if not passphrase:
            passphrase = getpass.getpass("バックアップのパスフレーズ: ")
            
        # 暗号化キーの生成
        key = self._derive_key(passphrase)
        fernet = Fernet(key)
        
        # バックアップ情報の読み込み
        info_path = backup_dir / 'backup-info.json'
        if info_path.exists():
            backup_info = json.loads(info_path.read_text())
            self.logger.info(f"バックアップ日時: {backup_info['timestamp']}")
            
        # SSH鍵の復元
        ssh_files = {
            'id_ed25519.encrypted': Path.home() / '.ssh' / 'id_ed25519',
            'id_ed25519.pub.encrypted': Path.home() / '.ssh' / 'id_ed25519.pub',
            'config.encrypted': Path.home() / '.ssh' / 'config'
        }
        
        for encrypted_name, target_path in ssh_files.items():
            encrypted_path = backup_dir / encrypted_name
            if encrypted_path.exists():
                self.logger.info(f"復元中: {target_path}")
                
                # 復号化
                encrypted_content = encrypted_path.read_bytes()
                content = fernet.decrypt(encrypted_content)
                
                # ターゲットディレクトリの作成
                target_path.parent.mkdir(mode=0o700, exist_ok=True)
                
                # ファイルの書き込み
                target_path.write_bytes(content)
                
                # 権限設定
                if 'pub' in encrypted_name:
                    os.chmod(target_path, 0o644)
                else:
                    os.chmod(target_path, 0o600)
                    
        # GPG鍵の復元
        gpg_backup_path = backup_dir / 'gpg-keys.asc'
        if gpg_backup_path.exists():
            self.logger.info("GPG鍵を復元中...")
            encrypted_gpg = gpg_backup_path.read_bytes()
            gpg_data = fernet.decrypt(encrypted_gpg).decode()
            
            # GPG鍵のインポート
            process = subprocess.Popen(
                ['gpg', '--import'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(gpg_data.encode())
            
            if process.returncode == 0:
                self.logger.info("✅ GPG鍵の復元が完了しました")
            else:
                self.logger.error(f"GPG鍵の復元エラー: {stderr.decode()}")
                
        self.logger.info("✅ 復元が完了しました")
        
    def _derive_key(self, passphrase):
        """パスフレーズから暗号化キーを生成"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'nix-mac-genesis-salt',  # 固定salt（実運用では改善が必要）
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        return key
        
    def _export_gpg_keys(self):
        """GPG鍵をエクスポート"""
        try:
            # 秘密鍵のエクスポート
            result = subprocess.run(
                ['gpg', '--armor', '--export-secret-keys'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                return result.stdout
            else:
                self.logger.warning("エクスポートするGPG鍵がありません")
                return None
                
        except Exception as e:
            self.logger.error(f"GPG鍵エクスポートエラー: {e}")
            return None
            
    def configure_ssh_agent(self):
        """SSH Agent設定"""
        self.logger.info("SSH Agent設定を構成中...")
        
        # launchd plistファイルの作成
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openssh.ssh-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/ssh-agent</string>
        <string>-l</string>
    </array>
    <key>Sockets</key>
    <dict>
        <key>Listeners</key>
        <dict>
            <key>SecureSocketWithKey</key>
            <string>SSH_AUTH_SOCK</string>
        </dict>
    </dict>
    <key>EnableTransactions</key>
    <true/>
</dict>
</plist>"""
        
        plist_path = Path.home() / 'Library/LaunchAgents/com.openssh.ssh-agent.plist'
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(plist_content)
        
        # launchdに登録
        try:
            subprocess.run(['launchctl', 'unload', str(plist_path)], capture_output=True)
            subprocess.run(['launchctl', 'load', '-w', str(plist_path)], check=True)
            self.logger.info("✅ SSH Agent設定が完了しました")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"SSH Agent設定エラー: {e}")
            
    def configure_gpg_agent(self):
        """GPG Agent設定"""
        self.logger.info("GPG Agent設定を構成中...")
        
        gpg_dir = Path.home() / '.gnupg'
        gpg_dir.mkdir(mode=0o700, exist_ok=True)
        
        # gpg-agent.conf
        agent_conf = """default-cache-ttl 600
max-cache-ttl 7200
enable-ssh-support
pinentry-program /usr/local/bin/pinentry-mac
"""
        
        agent_conf_path = gpg_dir / 'gpg-agent.conf'
        agent_conf_path.write_text(agent_conf)
        
        # gpg.conf
        gpg_conf = """use-agent
no-tty
"""
        
        gpg_conf_path = gpg_dir / 'gpg.conf'
        gpg_conf_path.write_text(gpg_conf)
        
        # GPG Agentの再起動
        try:
            subprocess.run(['gpgconf', '--kill', 'gpg-agent'], capture_output=True)
            subprocess.run(['gpgconf', '--launch', 'gpg-agent'], check=True)
            self.logger.info("✅ GPG Agent設定が完了しました")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"GPG Agent設定エラー: {e}")
