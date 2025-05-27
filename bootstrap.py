#!/usr/bin/env python3
"""
Nix-Darwin Mac初期設定Bootstrap
新しいMacでNix環境とGitHub連携を自動設定するエントリーポイント
"""

import sys
import os
import subprocess
import logging
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nix_installer import NixInstaller
from github_setup import GitHubSetup
from system_config import SystemConfigDetector
from security import SecurityManager
from utils import ColoredFormatter, confirm_action, check_command_exists


# Set up logging
def setup_logging(verbose=False):
    """ログ設定のセットアップ"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Console handler with color
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter())
    
    # File handler
    log_file = Path.home() / '.nix-mac-genesis.log'
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


class Bootstrap:
    """Bootstrap処理のメインクラス"""
    
    def __init__(self, logger):
        self.logger = logger
        self.nix_installer = NixInstaller(logger)
        self.github_setup = GitHubSetup(logger)
        self.system_config = SystemConfigDetector(logger)
        self.security_manager = SecurityManager(logger)
        
    def run(self, private_repo=None, skip_confirmations=False):
        """Bootstrap処理の実行"""
        try:
            self.logger.info("🚀 Nix-Darwin Mac初期設定を開始します")
            
            # Phase 1: システム準備
            self.logger.info("\n📦 Phase 1: システム準備")
            self._prepare_system(skip_confirmations)
            
            # Phase 2: Nixインストール
            self.logger.info("\n🔧 Phase 2: Nixインストール")
            self._install_nix(skip_confirmations)
            
            # Phase 3: GitHub連携設定
            self.logger.info("\n🔑 Phase 3: GitHub連携設定")
            self._setup_github(skip_confirmations)
            
            # Phase 4: Nix-Darwin設定
            self.logger.info("\n⚙️  Phase 4: Nix-Darwin設定")
            self._setup_nix_darwin(private_repo, skip_confirmations)
            
            self.logger.info("\n✅ Bootstrap処理が完了しました！")
            self.logger.info("🎉 新しいターミナルを開いて環境を確認してください")
            
        except Exception as e:
            self.logger.error(f"❌ Bootstrap処理中にエラーが発生しました: {e}")
            raise
            
    def _prepare_system(self, skip_confirmations):
        """システムの準備"""
        # macOS開発者ツールの確認
        if not check_command_exists('git'):
            self.logger.info("Xcodeコマンドラインツールをインストールします...")
            if skip_confirmations or confirm_action("Xcodeコマンドラインツールをインストールしますか？"):
                subprocess.run(['xcode-select', '--install'], check=False)
                input("インストールが完了したらEnterキーを押してください...")
        
        # 基本ディレクトリの作成
        dirs = [
            Path.home() / '.config',
            Path.home() / '.config/nix-darwin',
            Path.home() / '.ssh',
        ]
        
        for dir_path in dirs:
            if not dir_path.exists():
                self.logger.info(f"ディレクトリを作成: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
                
    def _install_nix(self, skip_confirmations):
        """Nixのインストール"""
        if check_command_exists('nix'):
            self.logger.info("Nixは既にインストールされています")
            return
            
        if skip_confirmations or confirm_action("Nixをインストールしますか？"):
            self.nix_installer.install_nix()
            self.nix_installer.setup_flakes()
            
    def _setup_github(self, skip_confirmations):
        """GitHub連携の設定"""
        # SSH鍵の生成・設定
        if skip_confirmations or confirm_action("SSH鍵を生成しますか？"):
            self.github_setup.generate_ssh_keys()
            
        # GPG鍵の生成・設定
        if skip_confirmations or confirm_action("GPG鍵を生成しますか？"):
            self.github_setup.setup_gpg()
            
        # GitHub CLI認証
        if skip_confirmations or confirm_action("GitHub CLIで認証しますか？"):
            self.github_setup.authenticate_gh()
            
        # Git設定
        self.github_setup.configure_git()
        
    def _setup_nix_darwin(self, private_repo, skip_confirmations):
        """Nix-Darwinの設定"""
        if not private_repo:
            private_repo = input("Nix-Darwin設定のprivateリポジトリURL（空でスキップ）: ").strip()
            
        if private_repo:
            # プライベートリポジトリからクローン
            config_dir = Path.home() / '.config/nix-darwin'
            if config_dir.exists() and any(config_dir.iterdir()):
                if not skip_confirmations and not confirm_action(f"{config_dir}は既に存在します。上書きしますか？"):
                    self.logger.info("Nix-Darwin設定のクローンをスキップしました")
                    return
                    
            self.logger.info(f"設定をクローン中: {private_repo}")
            subprocess.run(['git', 'clone', private_repo, str(config_dir)], check=True)
            
            # nix-darwinのインストールと適用
            if skip_confirmations or confirm_action("Nix-Darwin設定を適用しますか？"):
                self.nix_installer.install_nix_darwin()
                os.chdir(config_dir)
                subprocess.run(['nix', 'run', 'nix-darwin', '--', 'switch', '--flake', '.'], check=True)
        else:
            # デフォルトテンプレートから設定を生成
            self.logger.info("デフォルトテンプレートからNix-Darwin設定を生成します")
            self.system_config.generate_nix_config()
            
            if skip_confirmations or confirm_action("生成したNix-Darwin設定を適用しますか？"):
                self.nix_installer.install_nix_darwin()
                config_dir = Path.home() / '.config/nix-darwin'
                os.chdir(config_dir)
                subprocess.run(['nix', 'run', 'nix-darwin', '--', 'switch', '--flake', '.'], check=True)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='Nix-Darwin Mac初期設定Bootstrap'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細なログ出力を有効化'
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='全ての確認プロンプトに自動でYesと回答'
    )
    parser.add_argument(
        '--private-repo',
        help='Nix-Darwin設定のprivateリポジトリURL'
    )
    
    args = parser.parse_args()
    
    # ログ設定
    logger = setup_logging(args.verbose)
    
    # Bootstrap実行
    bootstrap = Bootstrap(logger)
    bootstrap.run(
        private_repo=args.private_repo,
        skip_confirmations=args.yes
    )


if __name__ == '__main__':
    main()
