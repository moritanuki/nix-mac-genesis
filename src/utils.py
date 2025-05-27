"""
ユーティリティ関数とヘルパークラス
"""

import subprocess
import logging
import sys
import os
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """カラー出力対応のログフォーマッター"""
    
    # ANSIカラーコード
    COLORS = {
        'DEBUG': '\033[36m',     # シアン
        'INFO': '\033[32m',      # 緑
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 赤
        'CRITICAL': '\033[35m',  # マゼンタ
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # ログレベルに応じた色を設定
        log_color = self.COLORS.get(record.levelname, self.RESET)
        
        # 絵文字の追加
        emoji = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️ ',
            'WARNING': '⚠️ ',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }.get(record.levelname, '')
        
        # メッセージのフォーマット
        record.levelname = f"{log_color}{emoji} {record.levelname}{self.RESET}"
        record.msg = f"{record.msg}"
        
        return super().format(record)


def confirm_action(prompt, default=True):
    """ユーザーに確認を求める"""
    default_str = 'Y/n' if default else 'y/N'
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
        
    return response in ['y', 'yes', 'はい']


def check_command_exists(command):
    """コマンドが存在するかチェック"""
    try:
        subprocess.run(
            ['which', command],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_command(command, check=True, capture_output=True, text=True, **kwargs):
    """コマンドを実行してログ出力"""
    logger = logging.getLogger(__name__)
    
    if isinstance(command, str):
        command = command.split()
        
    logger.debug(f"実行: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=text,
            **kwargs
        )
        
        if capture_output and result.stdout:
            logger.debug(f"出力: {result.stdout}")
            
        return result
        
    except subprocess.CalledProcessError as e:
        logger.error(f"コマンドエラー: {e}")
        if capture_output and e.stderr:
            logger.error(f"エラー出力: {e.stderr}")
        raise


def get_home_directory():
    """ホームディレクトリを取得"""
    return Path.home()


def ensure_directory(path, mode=0o755):
    """ディレクトリが存在することを保証"""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, mode=mode)
    return path


def is_macos():
    """macOSかどうかチェック"""
    return sys.platform == 'darwin'


def get_macos_version():
    """macOSのバージョンを取得"""
    if not is_macos():
        return None
        
    try:
        result = subprocess.run(
            ['sw_vers', '-productVersion'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None


def is_apple_silicon():
    """Apple Siliconマシンかどうかチェック"""
    if not is_macos():
        return False
        
    try:
        result = subprocess.run(
            ['uname', '-m'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() == 'arm64'
    except:
        return False


def get_current_shell():
    """現在のシェルを取得"""
    return os.environ.get('SHELL', '/bin/zsh')


def add_to_path(directory):
    """PATHに追加"""
    directory = str(Path(directory).expanduser().resolve())
    
    if directory not in os.environ.get('PATH', '').split(':'):
        os.environ['PATH'] = f"{directory}:{os.environ.get('PATH', '')}"


def create_symlink(source, target, force=False):
    """シンボリックリンクを作成"""
    source = Path(source)
    target = Path(target)
    
    if target.exists() or target.is_symlink():
        if force:
            target.unlink()
        else:
            raise FileExistsError(f"ターゲットが既に存在します: {target}")
            
    target.symlink_to(source)


def backup_file(file_path, suffix='.backup'):
    """ファイルのバックアップを作成"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return None
        
    backup_path = file_path.with_suffix(file_path.suffix + suffix)
    
    # 既存のバックアップがある場合は番号を付ける
    counter = 1
    while backup_path.exists():
        backup_path = file_path.with_suffix(f"{file_path.suffix}{suffix}.{counter}")
        counter += 1
        
    file_path.rename(backup_path)
    return backup_path


def read_json_file(file_path):
    """JSONファイルを読み込み"""
    import json
    
    file_path = Path(file_path)
    if not file_path.exists():
        return None
        
    with open(file_path, 'r') as f:
        return json.load(f)


def write_json_file(file_path, data, indent=2):
    """JSONファイルに書き込み"""
    import json
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)


def get_git_config(key, default=None):
    """Git設定値を取得"""
    try:
        result = subprocess.run(
            ['git', 'config', '--global', key],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() or default
    except:
        return default


def set_git_config(key, value):
    """Git設定値を設定"""
    subprocess.run(
        ['git', 'config', '--global', key, value],
        check=True
    )


def is_interactive():
    """対話的セッションかどうかチェック"""
    return sys.stdin.isatty()


def prompt_with_default(prompt, default=None):
    """デフォルト値付きでプロンプト"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
        
    response = input(prompt).strip()
    
    if not response and default:
        return default
        
    return response


def format_size(bytes_size):
    """バイトサイズを人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def get_terminal_size():
    """ターミナルサイズを取得"""
    try:
        import shutil
        return shutil.get_terminal_size()
    except:
        return (80, 24)


def print_progress(current, total, prefix='Progress:', suffix='Complete', length=50):
    """プログレスバーを表示"""
    percent = 100 * (current / float(total))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    
    print(f'\r{prefix} |{bar}| {percent:.1f}% {suffix}', end='', flush=True)
    
    if current == total:
        print()


class Spinner:
    """処理中のスピナー表示"""
    
    def __init__(self, message='Processing...'):
        self.message = message
        self.spinning = False
        self.thread = None
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        
    def start(self):
        """スピナーを開始"""
        import threading
        import time
        
        self.spinning = True
        
        def spin():
            spinner_chars = '|/-\\'
            idx = 0
            while self.spinning:
                print(f'\r{self.message} {spinner_chars[idx % len(spinner_chars)]}', end='', flush=True)
                idx += 1
                time.sleep(0.1)
                
        self.thread = threading.Thread(target=spin)
        self.thread.start()
        
    def stop(self):
        """スピナーを停止"""
        self.spinning = False
        if self.thread:
            self.thread.join()
        print('\r' + ' ' * (len(self.message) + 2), end='', flush=True)
        print('\r', end='', flush=True)
