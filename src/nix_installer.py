"""
Nixインストールと設定を管理するモジュール
"""

import subprocess
import os
import logging
from pathlib import Path
import tempfile
import requests


class NixInstaller:
    """Nixのインストールと設定を管理するクラス"""
    
    def __init__(self, logger):
        self.logger = logger
        self.nix_conf_dir = Path('/etc/nix')
        self.user_conf_dir = Path.home() / '.config/nix'
        
    def install_nix(self):
        """Determinate Systems installerを使用してNixをインストール"""
        self.logger.info("Determinate Systems InstallerでNixをインストール中...")
        
        try:
            # Determinate Systems installerをダウンロードして実行
            installer_url = "https://install.determinate.systems/nix"
            
            # curlでインストーラーを直接実行
            cmd = f"curl --proto '=https' --tlsv1.2 -sSf -L {installer_url} | sh -s -- install --no-confirm"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Nixインストールエラー: {result.stderr}")
                raise Exception("Nixのインストールに失敗しました")
                
            self.logger.info("✅ Nixのインストールが完了しました")
            
            # 環境変数の再読み込みを促す
            self.logger.info("ℹ️  新しいシェルセッションでNixが利用可能になります")
            
        except Exception as e:
            self.logger.error(f"Nixインストール中にエラー: {e}")
            raise
            
    def setup_flakes(self):
        """Nix Flakesを有効化"""
        self.logger.info("Nix Flakesを有効化中...")
        
        # nix.confの設定
        nix_conf_content = """# Nix configuration
experimental-features = nix-command flakes
auto-optimise-store = true
trusted-users = root @admin
"""
        
        # /etc/nix/nix.confに設定を追加
        if self.nix_conf_dir.exists():
            nix_conf_path = self.nix_conf_dir / 'nix.conf'
            
            # 既存の設定を読み込み
            existing_content = ""
            if nix_conf_path.exists():
                existing_content = nix_conf_path.read_text()
                
            # experimental-featuresが既に設定されているかチェック
            if 'experimental-features' not in existing_content:
                self.logger.info(f"設定を追加: {nix_conf_path}")
                
                # sudoで書き込み
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file.write(existing_content + '\n' + nix_conf_content)
                    temp_path = temp_file.name
                    
                subprocess.run(
                    ['sudo', 'cp', temp_path, str(nix_conf_path)],
                    check=True
                )
                os.unlink(temp_path)
            else:
                self.logger.info("Flakesは既に有効化されています")
                
        # ユーザー設定ディレクトリの作成
        self.user_conf_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("✅ Nix Flakesの設定が完了しました")
        
    def install_nix_darwin(self):
        """nix-darwinをインストール"""
        self.logger.info("nix-darwinをインストール中...")
        
        try:
            # nix-darwinのインストール
            cmd = [
                'nix', 'run', 'nix-darwin', '--experimental-features', 
                'nix-command flakes', '--', 'switch', '--flake', 
                str(Path.home() / '.config/nix-darwin')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # 初回インストールの場合はbootstrapが必要
                if "darwin-rebuild" not in result.stderr:
                    self.logger.info("初回インストールのためbootstrapを実行...")
                    self._bootstrap_nix_darwin()
                else:
                    self.logger.error(f"nix-darwinインストールエラー: {result.stderr}")
                    raise Exception("nix-darwinのインストールに失敗しました")
            else:
                self.logger.info("✅ nix-darwinのインストールが完了しました")
                
        except Exception as e:
            self.logger.error(f"nix-darwinインストール中にエラー: {e}")
            raise
            
    def _bootstrap_nix_darwin(self):
        """nix-darwinの初回bootstrap"""
        config_dir = Path.home() / '.config/nix-darwin'
        
        # 基本的なflake.nixが必要
        if not (config_dir / 'flake.nix').exists():
            self.logger.error("flake.nixが見つかりません")
            raise Exception("Nix-Darwin設定ファイルが見つかりません")
            
        # bootstrap実行
        self.logger.info("nix-darwin bootstrapを実行中...")
        
        cmd = [
            'nix', 'run', 'nix-darwin', '--experimental-features',
            'nix-command flakes', '--', 'switch', '--flake',
            str(config_dir)
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode != 0:
            raise Exception("nix-darwin bootstrapに失敗しました")
            
        self.logger.info("✅ nix-darwin bootstrapが完了しました")
        
    def verify_installation(self):
        """Nixインストールの検証"""
        self.logger.info("Nixインストールを検証中...")
        
        checks = {
            'nix': 'nix --version',
            'nix-env': 'nix-env --version',
            'nix-shell': 'nix-shell --version'
        }
        
        all_good = True
        
        for name, cmd in checks.items():
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    check=True
                )
                version = result.stdout.strip()
                self.logger.info(f"✅ {name}: {version}")
            except subprocess.CalledProcessError:
                self.logger.error(f"❌ {name}: 実行できません")
                all_good = False
                
        # Flakesの確認
        try:
            result = subprocess.run(
                ['nix', 'flake', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("✅ Flakes: 有効")
            else:
                self.logger.warning("⚠️  Flakes: 無効（新しいシェルで有効になります）")
        except:
            self.logger.warning("⚠️  Flakes: 確認できません")
            
        return all_good
