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
        """公式インストーラーを使用してNixをインストール"""
        self.logger.info("公式インストーラーでNixをインストール中...")
        
        try:
            # 公式Nixインストーラーをダウンロードして実行
            installer_url = "https://nixos.org/nix/install"
            
            # インストーラーをダウンロード
            self.logger.info("インストーラーをダウンロード中...")
            download_cmd = f"curl -L {installer_url} -o /tmp/install-nix.sh"
            subprocess.run(download_cmd, shell=True, check=True)
            
            # インストーラーに実行権限を付与
            subprocess.run(['chmod', '+x', '/tmp/install-nix.sh'], check=True)
            
            # インストーラーを実行（対話的に）
            self.logger.info("Nixインストーラーを実行します（sudoパスワードが必要です）")
            result = subprocess.run(
                ['sh', '/tmp/install-nix.sh', '--daemon'],
                check=False
            )
            
            if result.returncode != 0:
                self.logger.error("Nixインストールに失敗しました")
                raise Exception("Nixのインストールに失敗しました")
                
            self.logger.info("✅ Nixのインストールが完了しました")
            
            # 環境変数の再読み込み
            self.logger.info("環境変数を再読み込み中...")
            if Path('/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh').exists():
                subprocess.run([
                    'source',
                    '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'
                ], shell=True)
            
        except Exception as e:
            self.logger.error(f"Nixインストール中にエラー: {e}")
            raise
            
    def setup_flakes(self):
        """Nix Flakesを有効化"""
        self.logger.info("Nix Flakesを有効化中...")
        
        # nix.confの設定
        nix_conf_content = """experimental-features = nix-command flakes"""
        
        # /etc/nix/nix.confに設定を追加
        nix_conf_path = self.nix_conf_dir / 'nix.conf'
        
        try:
            # 既存の設定を読み込み
            existing_content = ""
            if nix_conf_path.exists():
                result = subprocess.run(
                    ['sudo', 'cat', str(nix_conf_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                existing_content = result.stdout
                
            # experimental-featuresが既に設定されているかチェック
            if 'experimental-features' not in existing_content:
                self.logger.info(f"設定を追加: {nix_conf_path}")
                
                # 設定を追加
                if existing_content and not existing_content.endswith('\n'):
                    existing_content += '\n'
                new_content = existing_content + nix_conf_content + '\n'
                
                # sudoで書き込み
                process = subprocess.Popen(
                    ['sudo', 'tee', str(nix_conf_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=new_content)
                
                if process.returncode != 0:
                    raise Exception(f"設定の書き込みに失敗: {stderr}")
                    
                # nix-daemonを再起動
                self.logger.info("nix-daemonを再起動中...")
                subprocess.run(['sudo', 'launchctl', 'kickstart', '-k', 'system/org.nixos.nix-daemon'], check=True)
                
            else:
                self.logger.info("Flakesは既に有効化されています")
                
        except Exception as e:
            self.logger.error(f"Flakes設定中にエラー: {e}")
            raise
            
        self.logger.info("✅ Nix Flakesの設定が完了しました")
        
    def install_nix_darwin(self):
        """nix-darwinをインストール"""
        self.logger.info("nix-darwinをインストール中...")
        
        try:
            # 環境変数を設定
            env = os.environ.copy()
            env['PATH'] = f"/nix/var/nix/profiles/default/bin:{env.get('PATH', '')}"
            
            # darwin-rebuildコマンドが存在するかチェック
            darwin_rebuild_exists = subprocess.run(
                ['which', 'darwin-rebuild'],
                capture_output=True,
                env=env
            ).returncode == 0
            
            if not darwin_rebuild_exists:
                # 初回インストール
                self.logger.info("nix-darwinの初回インストールを実行...")
                
                # nix-darwin用の設定ディレクトリを作成
                darwin_config_dir = Path.home() / '.config/nix-darwin'
                darwin_config_dir.mkdir(parents=True, exist_ok=True)
                
                # 基本的なflake.nixを作成（後でsystem_config.pyで更新される）
                if not (darwin_config_dir / 'flake.nix').exists():
                    self._create_initial_flake(darwin_config_dir)
                
                # ホスト名を取得
                hostname = subprocess.run(
                    ['hostname', '-s'],
                    capture_output=True,
                    text=True,
                    env=env
                ).stdout.strip()
                
                # nix-darwinをビルドしてインストール
                cmd = [
                    'nix', 'build', f'{darwin_config_dir}#darwinConfigurations.{hostname}.system',
                    '--extra-experimental-features', 'nix-command flakes'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode != 0:
                    self.logger.error(f"nix-darwinビルドエラー: {result.stderr}")
                    raise Exception("nix-darwinのビルドに失敗しました")
                
                # システムにインストール
                self.logger.info("nix-darwinをシステムにインストール中...")
                cmd = [
                    './result/sw/bin/darwin-rebuild', 'switch',
                    '--flake', str(darwin_config_dir)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode != 0:
                    self.logger.error(f"darwin-rebuild switchエラー: {result.stderr}")
                    raise Exception("darwin-rebuild switchに失敗しました")
                    
            else:
                # 既にインストール済みの場合は設定を適用
                self.logger.info("nix-darwinは既にインストール済み。設定を適用中...")
                darwin_config_dir = Path.home() / '.config/nix-darwin'
                
                cmd = [
                    'darwin-rebuild', 'switch',
                    '--flake', str(darwin_config_dir)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode != 0:
                    self.logger.error(f"darwin-rebuild switchエラー: {result.stderr}")
                    raise Exception("darwin-rebuild switchに失敗しました")
                    
            self.logger.info("✅ nix-darwinのインストール/設定が完了しました")
                
        except Exception as e:
            self.logger.error(f"nix-darwinインストール中にエラー: {e}")
            raise
            
    def _create_initial_flake(self, config_dir):
        """初期のflake.nixを作成"""
        hostname = subprocess.run(
            ['hostname', '-s'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        initial_flake = f'''{{
  description = "Darwin system configuration";

  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    darwin = {{
      url = "github:LnL7/nix-darwin";
      inputs.nixpkgs.follows = "nixpkgs";
    }};
  }};

  outputs = {{ self, nixpkgs, darwin }}: {{
    darwinConfigurations."{hostname}" = darwin.lib.darwinSystem {{
      system = "aarch64-darwin";
      modules = [ ./configuration.nix ];
    }};
  }};
}}
'''
        
        # flake.nixを作成
        with open(config_dir / 'flake.nix', 'w') as f:
            f.write(initial_flake)
            
        # 基本的なconfiguration.nixも作成
        initial_config = '''{ config, pkgs, ... }:

{
  # Auto upgrade nix package and the daemon service.
  services.nix-daemon.enable = true;
  nix.package = pkgs.nix;

  # Create /etc/zshrc that loads the nix-darwin environment.
  programs.zsh.enable = true;

  # Used for backwards compatibility, please read the changelog before changing.
  # $ darwin-rebuild changelog
  system.stateVersion = 4;
}
'''
        
        with open(config_dir / 'configuration.nix', 'w') as f:
            f.write(initial_config)
            
        self.logger.info("初期設定ファイルを作成しました")
        
    def verify_installation(self):
        """Nixインストールの検証"""
        self.logger.info("Nixインストールを検証中...")
        
        # PATH に Nix が含まれているか確認
        nix_path = Path('/nix/var/nix/profiles/default/bin')
        if not nix_path.exists():
            self.logger.error("❌ Nix バイナリディレクトリが見つかりません")
            return False
            
        # 環境変数を設定して nix コマンドを実行
        env = os.environ.copy()
        env['PATH'] = f"{nix_path}:{env.get('PATH', '')}"
        
        checks = {
            'nix': ['nix', '--version'],
            'nix-env': ['nix-env', '--version'],
            'nix-shell': ['nix-shell', '--version']
        }
        
        all_good = True
        
        for name, cmd in checks.items():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env
                )
                version = result.stdout.strip()
                self.logger.info(f"✅ {name}: {version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.error(f"❌ {name}: 実行できません")
                all_good = False
                
        # Flakesの確認
        try:
            result = subprocess.run(
                ['nix', '--extra-experimental-features', 'nix-command flakes', 'flake', '--version'],
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode == 0:
                self.logger.info("✅ Flakes: 有効")
            else:
                self.logger.warning("⚠️  Flakes: 無効（新しいシェルで有効になります）")
        except:
            self.logger.warning("⚠️  Flakes: 確認できません")
            
        return all_good
    
    def setup_nix_environment(self):
        """Nixの環境変数を設定"""
        self.logger.info("Nix環境変数を設定中...")
        
        # Nix環境スクリプトのパス
        nix_daemon_script = Path('/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh')
        
        if nix_daemon_script.exists():
            # 環境変数を設定
            os.environ['PATH'] = f"/nix/var/nix/profiles/default/bin:{os.environ.get('PATH', '')}"
            os.environ['NIX_SSL_CERT_FILE'] = "/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt"
            
            self.logger.info("✅ Nix環境変数を設定しました")
            return True
        else:
            self.logger.error("❌ Nix環境スクリプトが見つかりません")
            return False
    
    def install_essential_tools(self):
        """必要なツールをNixでインストール"""
        self.logger.info("必要なツールをインストール中...")
        
        try:
            # 環境変数を設定
            env = os.environ.copy()
            env['PATH'] = f"/nix/var/nix/profiles/default/bin:{env.get('PATH', '')}"
            
            # インストールするパッケージ
            packages = ['github-cli', 'gnupg', 'pinentry_mac']
            
            for package in packages:
                self.logger.info(f"インストール中: {package}")
                cmd = [
                    'nix-env', '-iA', f'nixpkgs.{package}',
                    '--extra-experimental-features', 'nix-command flakes'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode == 0:
                    self.logger.info(f"✅ {package}をインストールしました")
                else:
                    self.logger.warning(f"⚠️  {package}のインストールに失敗: {result.stderr}")
                    
        except Exception as e:
            self.logger.error(f"ツールのインストール中にエラー: {e}")
            raise
