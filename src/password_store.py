"""
password-storeのセットアップと管理を行うモジュール
"""

import subprocess
import os
import logging
from pathlib import Path


class PasswordStoreManager:
    """password-storeの設定と管理を行うクラス"""
    
    def __init__(self, logger):
        self.logger = logger
        self.password_store_dir = Path.home() / '.password-store'
        
    def setup_password_store(self, private_repo_url=None, gpg_key_id=None):
        """password-storeをセットアップ"""
        self.logger.info("password-storeをセットアップ中...")
        
        try:
            # GPGキーIDが指定されていない場合は取得
            if not gpg_key_id:
                gpg_key_id = self._get_gpg_key_id()
                if not gpg_key_id:
                    self.logger.error("GPGキーが見つかりません。先にGPGキーを生成してください。")
                    return False
            
            # password-storeの初期化
            if not self.password_store_dir.exists():
                self.logger.info(f"password-storeを初期化中（GPGキー: {gpg_key_id}）")
                result = subprocess.run(
                    ['pass', 'init', gpg_key_id],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"password-store初期化エラー: {result.stderr}")
                    return False
                    
                self.logger.info("✅ password-storeを初期化しました")
            
            # プライベートリポジトリからのクローン
            if private_repo_url:
                self._clone_password_store(private_repo_url)
            else:
                # 新規リポジトリとして設定
                self._init_git_repo()
                
            self.logger.info("✅ password-storeのセットアップが完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"password-storeセットアップ中にエラー: {e}")
            return False
            
    def _get_gpg_key_id(self):
        """GPGキーIDを取得"""
        try:
            result = subprocess.run(
                ['gpg', '--list-secret-keys', '--keyid-format', 'LONG'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                # 最初の秘密鍵のIDを取得
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    if 'sec' in line and i + 1 < len(lines):
                        # 次の行からキーIDを取得
                        key_info = lines[i + 1].strip()
                        return key_info
                        
        except Exception as e:
            self.logger.debug(f"GPGキーID取得エラー: {e}")
            
        return None
        
    def _clone_password_store(self, repo_url):
        """プライベートリポジトリからpassword-storeをクローン"""
        self.logger.info("既存のpassword-storeリポジトリをクローン中...")
        
        # 既存のディレクトリをバックアップ
        if self.password_store_dir.exists():
            backup_dir = self.password_store_dir.with_suffix('.backup')
            self.logger.info(f"既存のディレクトリをバックアップ: {backup_dir}")
            self.password_store_dir.rename(backup_dir)
            
        try:
            # リポジトリをクローン
            result = subprocess.run(
                ['git', 'clone', repo_url, str(self.password_store_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"クローンエラー: {result.stderr}")
                # バックアップを復元
                if backup_dir.exists():
                    backup_dir.rename(self.password_store_dir)
                return False
                
            self.logger.info("✅ password-storeリポジトリをクローンしました")
            
            # バックアップを削除
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
                
            return True
            
        except Exception as e:
            self.logger.error(f"クローン中にエラー: {e}")
            return False
            
    def _init_git_repo(self):
        """password-storeディレクトリをGitリポジトリとして初期化"""
        self.logger.info("password-storeディレクトリをGitリポジトリとして初期化中...")
        
        os.chdir(self.password_store_dir)
        
        try:
            # Git初期化
            subprocess.run(['git', 'init'], check=True)
            
            # .gitignoreを作成
            gitignore_content = """# macOS
.DS_Store

# Temporary files
*.tmp
*.swp
*~

# GPG
*.gpg
!.gpg-id
"""
            gitignore_path = self.password_store_dir / '.gitignore'
            gitignore_path.write_text(gitignore_content)
            
            # 初期コミット
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(
                ['git', 'commit', '-m', 'Initial password-store setup'],
                check=True
            )
            
            self.logger.info("✅ Gitリポジトリを初期化しました")
            
        except Exception as e:
            self.logger.error(f"Git初期化中にエラー: {e}")
            
    def configure_gpg_for_pass(self):
        """password-store用のGPG設定"""
        self.logger.info("password-store用のGPG設定を構成中...")
        
        # GPG Agentの設定
        gpg_agent_conf = Path.home() / '.gnupg' / 'gpg-agent.conf'
        gpg_agent_conf.parent.mkdir(parents=True, exist_ok=True)
        
        gpg_agent_content = """# GPG Agent configuration for macOS
default-cache-ttl 3600
max-cache-ttl 86400
pinentry-program /opt/homebrew/bin/pinentry-mac
"""
        
        if not gpg_agent_conf.exists():
            gpg_agent_conf.write_text(gpg_agent_content)
            self.logger.info("✅ GPG Agent設定を作成しました")
            
        # GPG Agentを再起動
        try:
            subprocess.run(['gpgconf', '--kill', 'gpg-agent'], check=True)
            self.logger.info("✅ GPG Agentを再起動しました")
        except:
            self.logger.debug("GPG Agent再起動をスキップ")
            
    def add_password_store_aliases(self):
        """便利なエイリアスを追加"""
        aliases = {
            'pw': 'pass',
            'pwg': 'pass generate',
            'pws': 'pass show',
            'pwf': 'pass find',
            'pwc': 'pass show -c',  # クリップボードにコピー
            'pwgit': 'pass git',
        }
        
        return aliases
        
    def verify_setup(self):
        """password-storeのセットアップを検証"""
        self.logger.info("password-storeのセットアップを検証中...")
        
        checks = []
        
        # password-storeディレクトリの存在確認
        if self.password_store_dir.exists():
            self.logger.info("✅ password-storeディレクトリが存在します")
            checks.append(True)
        else:
            self.logger.error("❌ password-storeディレクトリが見つかりません")
            checks.append(False)
            
        # .gpg-idファイルの確認
        gpg_id_file = self.password_store_dir / '.gpg-id'
        if gpg_id_file.exists():
            self.logger.info("✅ .gpg-idファイルが存在します")
            checks.append(True)
        else:
            self.logger.error("❌ .gpg-idファイルが見つかりません")
            checks.append(False)
            
        # passコマンドの動作確認
        try:
            result = subprocess.run(
                ['pass', 'ls'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("✅ passコマンドが正常に動作しています")
                checks.append(True)
            else:
                self.logger.error("❌ passコマンドの実行に失敗しました")
                checks.append(False)
        except:
            self.logger.error("❌ passコマンドが見つかりません")
            checks.append(False)
            
        return all(checks)