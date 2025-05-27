# Nix-Mac-Genesis

Nixを使ってMacBookの初期設定を完全自動化するPythonアプリケーション。新しいMacでGitHub連携まで設定し、その後はprivateリポジトリからnix-darwin設定を取得して完全な開発環境を構築します。

## 🚀 クイックスタート

新しいMacで以下のコマンドを実行：

```bash
# GitHubから取得
curl -o bootstrap.py https://github.com/[username]/nix-mac-genesis/raw/main/bootstrap.py
python3 bootstrap.py
```

## 📋 機能

### Phase 1: Bootstrap（Python）
- ✅ Nixインストール（Determinate Systems installer使用）
- ✅ SSH鍵生成・GitHub登録
- ✅ GPG鍵生成・設定
- ✅ GitHub CLI認証
- ✅ Gitグローバル設定

### Phase 2: Nix-Darwin設定
- ✅ 現在のmacOS設定を自動検出
- ✅ Nix-Darwin設定ファイルを生成
- ✅ 開発ツールの一括インストール
- ✅ システム設定の自動適用

## 🛠️ インストールされるツール

### Nixパッケージ
- Git, GitHub CLI
- Neovim, Tmux
- Ripgrep, fd, bat, eza
- Node.js, Python
- Docker CLI, Colima

### Homebrew Casks
- Warp (Terminal)
- Raycast
- Visual Studio Code
- Firefox Developer Edition
- 1Password

## 📁 プロジェクト構造

```
nix-mac-genesis/
├── bootstrap.py           # エントリーポイント
├── src/
│   ├── nix_installer.py   # Nix環境構築
│   ├── github_setup.py    # GitHub連携
│   ├── system_config.py   # システム設定検出
│   ├── security.py        # セキュリティ管理
│   └── utils.py           # ユーティリティ
├── config/
│   └── default_settings.yaml
└── requirements.txt
```

## 🔧 使用方法

### 基本的な使用

```bash
python3 bootstrap.py
```

### オプション

```bash
# 詳細ログを表示
python3 bootstrap.py -v

# 全ての確認を自動でYes
python3 bootstrap.py -y

# プライベートリポジトリを指定
python3 bootstrap.py --private-repo git@github.com:username/dotfiles.git
```

### 既存設定からの復元

プライベートリポジトリにNix-Darwin設定がある場合：

```bash
python3 bootstrap.py --private-repo git@github.com:username/my-nix-config.git
```

## 🔐 セキュリティ機能

- SSH鍵の自動生成と安全な管理
- GPG鍵によるGitコミット署名
- macOSキーチェーン統合
- 鍵の暗号化バックアップ機能

## 📝 カスタマイズ

`config/default_settings.yaml`を編集して、デフォルト設定をカスタマイズできます：

- システム設定のデフォルト値
- インストールするパッケージリスト
- VS Code拡張機能
- Zshプラグイン

## 🔄 生成されるNix設定

Bootstrap実行後、`~/.config/nix-darwin/`に以下のファイルが生成されます：

- `flake.nix` - Flake定義
- `darwin-configuration.nix` - メイン設定
- `home.nix` - Home Manager設定
- `modules/` - モジュール化された設定

## ⚡ トラブルシューティング

### Nixインストールが失敗する場合

```bash
# 既存のNixをアンインストール
/nix/nix-installer uninstall
```

### SSH鍵の問題

```bash
# SSH Agentの状態確認
ssh-add -l

# キーチェーンから再読み込み
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

## 📄 ライセンス

MIT License

## 🤝 貢献

プルリクエストを歓迎します！大きな変更の場合は、まずissueを作成して変更内容について議論してください。
