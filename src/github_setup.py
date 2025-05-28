"""
GitHub連携設定を管理するモジュール
"""

import subprocess
import os
import logging
from pathlib import Path
import getpass
import platform


class GitHubSetup:
    """GitHub連携の設定を管理するクラス"""
    
    def __init__(self, logger):
        self.logger = logger
        self.ssh_dir = Path.home() / '.ssh'
        self.ssh_key_path = self.ssh_dir / 'id_ed25519'
        self.ssh_pub_key_path = self.ssh_dir / 'id_ed25519.pub'
        
    def generate_ssh_keys(self):
        """SSH鍵を生成してGitHubに登録"""
        self.logger.info("SSH鍵を生成中...")
        
        # .sshディレクトリの作成
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        # 既存の鍵をチェック
        if self.ssh_key_path.exists():
            self.logger.warning("SSH鍵は既に存在します")
            use_existing = input("既存の鍵を使用しますか？ [Y/n]: ").strip().lower()
            if use_existing != 'n':
                self._add_ssh_to_agent()
                self._upload_ssh_to_github()
                return
                
        # メールアドレスの取得
        email = input("GitHubに登録されているメールアドレス: ").strip()
        if not email:
            raise ValueError("メールアドレスが必要です")
            
        # SSH鍵の生成
        try:
            cmd = [
                'ssh-keygen',
                '-t', 'ed25519',
                '-C', email,
                '-f', str(self.ssh_key_path),
                '-N', ''  # パスフレーズなし（後で設定可能）
            ]
            
            subprocess.run(cmd, check=True)
            self.logger.info("✅ SSH鍵の生成が完了しました")
            
            # 権限設定
            os.chmod(self.ssh_key_path, 0o600)
            os.chmod(self.ssh_pub_key_path, 0o644)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"SSH鍵生成エラー: {e}")
            raise
            
        # SSH設定ファイルの作成
        self._create_ssh_config()
        
        # SSH Agentに追加
        self._add_ssh_to_agent()
        
        # GitHubに公開鍵を登録
        self._upload_ssh_to_github()
        
    def _create_ssh_config(self):
        """SSH設定ファイルを作成"""
        ssh_config_path = self.ssh_dir / 'config'
        
        config_content = """# GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    AddKeysToAgent yes
    UseKeychain yes
"""
        
        if ssh_config_path.exists():
            existing_content = ssh_config_path.read_text()
            if 'github.com' in existing_content:
                self.logger.info("GitHub用SSH設定は既に存在します")
                return
                
            config_content = existing_content + '\n' + config_content
            
        self.logger.info("SSH設定ファイルを作成中...")
        ssh_config_path.write_text(config_content)
        os.chmod(ssh_config_path, 0o600)
        
    def _add_ssh_to_agent(self):
        """SSH鍵をSSH Agentに追加"""
        self.logger.info("SSH鍵をSSH Agentに追加中...")
        
        # macOSのキーチェーンに追加
        if platform.system() == 'Darwin':
            cmd = ['ssh-add', '--apple-use-keychain', str(self.ssh_key_path)]
        else:
            cmd = ['ssh-add', str(self.ssh_key_path)]
            
        try:
            subprocess.run(cmd, check=True)
            self.logger.info("✅ SSH鍵をSSH Agentに追加しました")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"SSH Agent追加時の警告: {e}")
            
    def _upload_ssh_to_github(self):
        """SSH公開鍵をGitHubに登録"""
        self.logger.info("SSH公開鍵をGitHubに登録中...")
        
        # 公開鍵の内容を取得
        pub_key_content = self.ssh_pub_key_path.read_text().strip()
        
        # GitHub CLIがインストールされているか確認（Nixパスも含めて）
        gh_found = False
        for path in ['/nix/var/nix/profiles/default/bin/gh', 'gh']:
            try:
                subprocess.run([path, '--version'], capture_output=True, check=True)
                gh_cmd = path
                gh_found = True
                break
            except:
                continue
                
        if not gh_found:
            self.logger.warning("GitHub CLIがインストールされていません")
            self.logger.info("手動で以下の公開鍵をGitHubに登録してください:")
            self.logger.info(f"\n{pub_key_content}\n")
            return
            
        # GitHub CLIで鍵を追加
        hostname = platform.node() or 'MacBook'
        key_title = f"{hostname} - nix-mac-genesis"
        
        try:
            cmd = [gh_cmd, 'ssh-key', 'add', str(self.ssh_pub_key_path), '--title', key_title]
            subprocess.run(cmd, check=True)
            self.logger.info("✅ SSH公開鍵をGitHubに登録しました")
        except subprocess.CalledProcessError:
            self.logger.warning("GitHub CLIでの鍵登録に失敗しました")
            self.logger.info("手動で以下の公開鍵をGitHubに登録してください:")
            self.logger.info(f"\n{pub_key_content}\n")
            
    def setup_gpg(self):
        """GPG鍵を生成してGitHubに登録"""
        self.logger.info("GPG鍵を生成中...")
        
        # GPGがインストールされているか確認（Nixパスも含めて）
        gpg_found = False
        for path in ['/nix/var/nix/profiles/default/bin/gpg', 'gpg']:
            try:
                subprocess.run([path, '--version'], capture_output=True, check=True)
                gpg_cmd = path
                gpg_found = True
                break
            except:
                continue
                
        if not gpg_found:
            self.logger.error("GPGがインストールされていません")
            self.logger.info("Nixでgpgをインストールしてください")
            return
            
        # 既存の鍵をチェック
        result = subprocess.run(
            [gpg_cmd, '--list-secret-keys', '--keyid-format', 'LONG'],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            self.logger.info("既存のGPG鍵が見つかりました")
            use_existing = input("既存の鍵を使用しますか？ [Y/n]: ").strip().lower()
            if use_existing != 'n':
                self._configure_git_gpg()
                return
                
        # GPG鍵の生成
        name = input("フルネーム: ").strip()
        email = input("メールアドレス: ").strip()
        
        if not name or not email:
            raise ValueError("名前とメールアドレスが必要です")
            
        # バッチファイルを作成
        batch_content = f"""
%echo Generating GPG key
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: {name}
Name-Email: {email}
Expire-Date: 2y
%commit
%echo done
"""
        
        batch_file = Path('/tmp/gpg_batch')
        batch_file.write_text(batch_content)
        
        try:
            # GPG鍵生成
            subprocess.run(
                [gpg_cmd, '--batch', '--generate-key', str(batch_file)],
                check=True
            )
            self.logger.info("✅ GPG鍵の生成が完了しました")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"GPG鍵生成エラー: {e}")
            raise
        finally:
            batch_file.unlink()
            
        # Git設定
        self._configure_git_gpg()
        
        # GitHubに公開鍵を登録
        self._upload_gpg_to_github(email)
        
    def _configure_git_gpg(self):
        """GitでGPG署名を設定"""
        self.logger.info("GitのGPG設定を構成中...")
        
        # GPG鍵IDを取得
        result = subprocess.run(
            ['gpg', '--list-secret-keys', '--keyid-format', 'LONG'],
            capture_output=True,
            text=True
        )
        
        # 鍵IDを抽出（例: sec   rsa4096/XXXXXXXXXXXXXXXX）
        key_id = None
        for line in result.stdout.split('\n'):
            if line.startswith('sec'):
                parts = line.split('/')
                if len(parts) > 1:
                    key_id = parts[1].split()[0]
                    break
                    
        if not key_id:
            self.logger.error("GPG鍵IDが見つかりません")
            return
            
        # Gitに設定
        subprocess.run(['git', 'config', '--global', 'user.signingkey', key_id], check=True)
        subprocess.run(['git', 'config', '--global', 'commit.gpgsign', 'true'], check=True)
        
        self.logger.info(f"✅ Git GPG署名を設定しました (Key ID: {key_id})")
        
    def _upload_gpg_to_github(self, email):
        """GPG公開鍵をGitHubに登録"""
        self.logger.info("GPG公開鍵をGitHubに登録中...")
        
        # 公開鍵をエクスポート
        result = subprocess.run(
            ['gpg', '--armor', '--export', email],
            capture_output=True,
            text=True
        )
        
        if not result.stdout:
            self.logger.error("GPG公開鍵のエクスポートに失敗しました")
            return
            
        # GitHub CLIで登録を試みる
        try:
            # 一時ファイルに保存
            gpg_pub_file = Path('/tmp/gpg_pub.asc')
            gpg_pub_file.write_text(result.stdout)
            
            subprocess.run(
                ['gh', 'gpg-key', 'add', str(gpg_pub_file)],
                check=True
            )
            self.logger.info("✅ GPG公開鍵をGitHubに登録しました")
            
            gpg_pub_file.unlink()
            
        except subprocess.CalledProcessError:
            self.logger.warning("GitHub CLIでのGPG鍵登録に失敗しました")
            self.logger.info("手動で以下のGPG公開鍵をGitHubに登録してください:")
            self.logger.info(f"\n{result.stdout}\n")
            
    def configure_git(self):
        """Gitのグローバル設定"""
        self.logger.info("Gitグローバル設定を構成中...")
        
        # 現在の設定を確認
        current_name = subprocess.run(
            ['git', 'config', '--global', 'user.name'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        current_email = subprocess.run(
            ['git', 'config', '--global', 'user.email'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        # 名前の設定
        if not current_name:
            default_name = os.environ.get('GIT_USER_NAME', 'moritanuki')
            name = input(f"Gitユーザー名 [{default_name}]: ").strip() or default_name
            if name:
                subprocess.run(['git', 'config', '--global', 'user.name', name], check=True)
                
        # メールアドレスの設定
        if not current_email:
            default_email = os.environ.get('GIT_USER_EMAIL', '82251856+moritanuki@users.noreply.github.com')
            email = input(f"Gitメールアドレス [{default_email}]: ").strip() or default_email
            if email:
                subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)
                
        # その他の推奨設定
        git_configs = {
            'init.defaultBranch': 'main',
            'pull.rebase': 'false',
            'core.editor': 'vim',
            'color.ui': 'auto',
            'push.autoSetupRemote': 'true'
        }
        
        for key, value in git_configs.items():
            subprocess.run(['git', 'config', '--global', key, value], check=True)
            
        self.logger.info("✅ Gitグローバル設定が完了しました")
        
    def authenticate_gh(self):
        """GitHub CLIで認証"""
        self.logger.info("GitHub CLIで認証中...")
        
        # ghがインストールされているか確認
        try:
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
        except:
            self.logger.error("GitHub CLIがインストールされていません")
            self.logger.info("Nixでghをインストールしてください")
            return
            
        # 認証状態を確認
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            self.logger.info("既にGitHub CLIで認証済みです")
            return
            
        # 認証実行
        self.logger.info("GitHub認証を開始します...")
        self.logger.info("ブラウザが開きます。GitHubにログインして認証を完了してください。")
        
        try:
            subprocess.run(
                ['gh', 'auth', 'login', '-h', 'github.com', '-p', 'ssh', '-w'],
                check=True
            )
            self.logger.info("✅ GitHub CLI認証が完了しました")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"GitHub CLI認証エラー: {e}")
            raise
