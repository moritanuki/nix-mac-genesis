# Nix-Darwin Mac初期設定システム開発要件

## プロジェクト概要
Nixを使ってMacBookの初期設定を完全自動化するPythonアプリケーション。新しいMacでGitHub連携まで設定し、その後はprivateリポジトリからnix-darwin設定を取得して完全な開発環境を構築する。

## Repository名
```
nix-mac-genesis
```

## 復元戦略

### Phase 1: Bootstrap（手動実行 - Python）
GoogleDriveまたはGitHubに保存された軽量なPythonスクリプトで基本環境を構築

#### 実行手順
```bash
# Google DriveまたはGitHubから取得
curl -o bootstrap.py https://github.com/[username]/nix-mac-genesis/raw/main/bootstrap.py
python3 bootstrap.py
```

#### Bootstrap機能
- Nixインストール（Determinate Systems installer使用）
- 基本的なGitHub設定（SSH鍵生成・登録、GPG設定）
- GitHubからprivateリポジトリのアクセス権確立

### Phase 2: 完全設定（Nix-Darwin）
GitHubのprivateリポジトリからnix-darwinフレーク設定を取得し、完全な環境を構築

## 技術スタック

### 開発言語
- **メイン**: Python 3.11+
- **設定管理**: Nix flakes + nix-darwin
- **システム設定**: Nix expressions

### パッケージ管理戦略
- **主要**: Nix packages（nixpkgs）
- **補完**: Homebrew（Nixで管理できないmacOSアプリのみ）
- **Mac App Store**: nix-darwinのmas連携

## 機能要件

### 1. Bootstrap段階（Python）

#### システム準備
- macOS開発者ツール確認・インストール
- Nixインストール（Determinate Systems installer）
- 基本ディレクトリ構造作成

#### GitHub連携設定
- SSH鍵生成（Ed25519）
- SSH設定ファイル作成
- GPG鍵生成・設定
- GitHub CLI (`gh`)インストール・認証
- Gitグローバル設定

#### セキュリティ設定
- macOSキーチェーン設定
- SSH Agent設定
- GPG Agent設定

### 2. Nix-Darwin設定段階

#### 開発ツール
- **エディタ**: Visual Studio Code + 拡張機能
- **ターミナル**: Warp
- **ブラウザ**: Firefox Developer Edition
- **ランチャー**: Raycast
- **コンテナ**: Colima + Docker CLI
- **その他**: Claude Code CLI, gh CLI

#### システム設定
現在のmacOS設定値に基づいた自動設定：

```nix
# Dock設定
system.defaults.dock = {
  autohide = true;
  autohide-delay = 0.1;
  autohide-time-modifier = 0.5;
  tilesize = 48;
  orientation = "bottom";
  show-recents = false;
  static-only = true;  # アクティブなアプリのみ表示
  mineffect = "scale";
};

# Finder設定  
system.defaults.finder = {
  AppleShowAllFiles = true;
  ShowStatusBar = true;
  ShowPathbar = true;
  FXDefaultSearchScope = "SCcf"; # 現在のフォルダ内を検索
  FXPreferredViewStyle = "Nlsv"; # リスト表示
};

# システム設定
system.defaults.NSGlobalDomain = {
  AppleShowAllExtensions = true;
  ApplePressAndHoldEnabled = false; # キーリピート有効
  KeyRepeat = 2;
  InitialKeyRepeat = 15;
  AppleInterfaceStyle = "Dark"; # ダークモード
};
```

#### Nix設定構造
```
~/.config/nix-darwin/
├── flake.nix              # メインフレーク定義
├── flake.lock             # 依存関係固定
├── darwin-configuration.nix # システム設定
├── home.nix               # ユーザー環境設定
└── modules/
    ├── homebrew.nix       # Homebrew管理
    ├── packages.nix       # パッケージ定義
    └── system.nix         # システム設定詳細
```

## 実装アーキテクチャ

### Pythonアプリ構造
```
nix-mac-genesis/
├── bootstrap.py           # エントリーポイント
├── src/
│   ├── __init__.py
│   ├── nix_installer.py   # Nix環境構築
│   ├── github_setup.py    # GitHub連携
│   ├── system_config.py   # システム設定取得
│   ├── security.py        # 暗号化・セキュリティ
│   └── utils.py           # ユーティリティ
├── templates/
│   ├── flake.nix.template
│   ├── darwin-configuration.nix.template
│   └── home.nix.template
├── config/
│   └── default_settings.yaml
└── requirements.txt
```

### 核となる機能モジュール

#### 1. Nixインストーラー (`nix_installer.py`)
```python
class NixInstaller:
    def install_nix(self):
        """Determinate Systems installerでNixをインストール"""
        
    def setup_flakes(self):
        """Flakes機能を有効化"""
        
    def install_nix_darwin(self):
        """nix-darwinをインストール"""
```

#### 2. GitHub設定 (`github_setup.py`)
```python
class GitHubSetup:
    def generate_ssh_keys(self):
        """SSH鍵生成・GitHub登録"""
        
    def setup_gpg(self):
        """GPG鍵生成・GitHub登録"""
        
    def configure_git(self):
        """Gitグローバル設定"""
        
    def authenticate_gh(self):
        """GitHub CLI認証"""
```

#### 3. システム設定検出 (`system_config.py`)
```python
class SystemConfigDetector:
    def read_current_dock_settings(self):
        """現在のDock設定を読み取り"""
        
    def read_current_finder_settings(self):
        """現在のFinder設定を読み取り"""
        
    def generate_nix_config(self):
        """現在の設定からNix設定を生成"""
```

## セキュリティ要件

### 暗号化保存
- SSH秘密鍵の暗号化バックアップ
- GPG鍵の安全な保存
- GitHub Personal Access Tokenの管理

### アクセス制御
- macOSキーチェーンアクセス管理
- SSH Agent forwarding設定
- GPG Agent設定

## Nix-Darwin設定要件

### パッケージ管理
```nix
environment.systemPackages = with pkgs; [
  # 開発ツール
  git
  gh
  vscode
  firefox-devedition-bin
  
  # コンテナ関連
  colima
  docker
  
  # ユーティリティ
  curl
  wget
  htop
  tree
  jq
];

# Homebrew管理（Nixで対応できないもののみ）
homebrew = {
  enable = true;
  casks = [
    "warp"
    "raycast"
  ];
};
```

### サービス設定
```nix
services = {
  nix-daemon.enable = true;
  
  # SSH Agent
  ssh-agent.enable = true;
  
  # GPG Agent  
  gpg-agent = {
    enable = true;
    enableSSHSupport = true;
  };
};
```

## 実行フロー

### 新しいMacでの実行手順
1. **Bootstrap実行**
   ```bash
   curl -o bootstrap.py https://github.com/[username]/nix-mac-genesis/raw/main/bootstrap.py
   python3 bootstrap.py
   ```

2. **対話的設定**
   - GitHub認証情報入力
   - SSH/GPGキー生成確認
   - プライベートリポジトリ指定

3. **Nix-Darwin自動実行**
   ```bash
   # bootstrapが自動実行
   git clone [private-repo] ~/.config/nix-darwin
   cd ~/.config/nix-darwin
   nix run nix-darwin -- switch --flake .
   ```

4. **完了確認**
   - 全アプリケーションのインストール確認
   - Claude Code CLIの動作確認
   - システム設定の適用確認

## エラーハンドリング

### 復旧機能
- 段階的なロールバック機能
- 設定ファイルのバックアップ
- Nix世代管理の活用

### ログ管理
- 詳細な実行ログ
- エラー時のデバッグ情報収集
- 設定変更の追跡

## 成功基準
- **完全自動化**: 最小限の手動入力でフル環境構築
- **再現性**: 複数台のMacで同一環境が構築される
- **高速性**: 初期設定完了まで20分以内
- **信頼性**: エラー時も適切に復旧可能
- **Claude Code動作**: 最終的にClaude Code CLIが使用可能

## 実装フェーズ

### Phase 1: Bootstrap Python開発
- GitHub連携機能
- Nixインストール機能
- 基本的なエラーハンドリング

### Phase 2: Nix-Darwin設定テンプレート
- フレーク設定作成
- システム設定の自動検出
- パッケージ定義

### Phase 3: 統合・テスト
- 全体フローの統合
- 複数環境でのテスト
- ドキュメント整備

### Phase 4: 運用改善
- エラーハンドリング強化
- ユーザビリティ向上
- 継続的なメンテナンス
