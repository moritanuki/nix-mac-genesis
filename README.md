# Nix-Mac-Genesis

Nixを使ってMacBookの初期設定を完全自動化するPythonアプリケーション。新しいMacでGitHub連携まで設定し、その後はprivateリポジトリからnix-darwin設定を取得して完全な開発環境を構築します。

## 🚀 クイックスタート

新しいMacで以下のコマンドを実行するだけで、完全な開発環境が構築されます：

```bash
# リポジトリをクローン
git clone https://github.com/moritanuki/nix-mac-genesis.git
cd nix-mac-genesis

# Bootstrap実行（全自動モード）
python3 bootstrap.py -y

# または、対話的に実行
python3 bootstrap.py
```

### ⚡ 完全自動実行の流れ

1. **Nixインストール**: 公式インストーラーを使用してNixをインストール
2. **環境設定**: Nix環境変数を自動設定、Flakesを有効化
3. **必須ツール**: GitHub CLI、GPG、pinentry_macを自動インストール
4. **GitHub設定**: SSH鍵生成、GPG鍵生成、Git設定を自動化
5. **Nix-Darwin**: 設定ファイルを生成して開発環境を構築

## 📋 機能

### Phase 1: Bootstrap（Python）
- ✅ Nixインストール（公式インストーラー使用、マルチユーザーインストール）
- ✅ Nix環境変数の自動設定（PATHなど）
- ✅ Nix Flakes有効化
- ✅ 必須ツールの自動インストール（GitHub CLI、GPG、pinentry_mac）
- ✅ SSH鍵生成・GitHub登録
- ✅ GPG鍵生成・設定
- ✅ GitHub CLI認証
- ✅ Gitグローバル設定
- ✅ password-storeセットアップ

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
- pass (password-store), GnuPG

### Homebrew Casks
- Warp (Terminal)
- Raycast
- Visual Studio Code
- Firefox Developer Edition

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

### 推奨: 完全自動実行

```bash
# 全ての確認を自動でYes（推奨）
python3 bootstrap.py -y
```

このコマンドで以下が自動的に実行されます：
- ✅ Nixのインストール（対話的な部分も自動応答）
- ✅ 環境変数の自動設定（再起動不要）
- ✅ GitHub CLI、GPG、pinentry_macの自動インストール
- ✅ SSH鍵とGPG鍵の生成（デフォルト設定使用）
- ✅ Nix-Darwin設定の生成と適用

### その他のオプション

```bash
# 詳細ログを表示
python3 bootstrap.py -v

# プライベートリポジトリを指定
python3 bootstrap.py --private-repo git@github.com:moritanuki/dotfiles.git

# 全オプションを組み合わせ
python3 bootstrap.py -y -v --private-repo git@github.com:moritanuki/dotfiles.git
```

### 環境変数

以下の環境変数を設定することで、デフォルト値をカスタマイズできます：

```bash
# GitHubユーザー名（デフォルト: moritanuki）
export GITHUB_USERNAME=your-username

# Gitユーザー名（デフォルト: moritanuki）
export GIT_USER_NAME="Your Name"

# Gitメールアドレス（デフォルト: 82251856+moritanuki@users.noreply.github.com）
export GIT_USER_EMAIL="your-email@example.com"
```

### 既存設定からの復元

プライベートリポジトリにNix-Darwin設定がある場合：

```bash
python3 bootstrap.py --private-repo git@github.com:moritanuki/my-nix-config.git
```

## 🔐 セキュリティ機能

- SSH鍵の自動生成と安全な管理
- GPG鍵によるGitコミット署名
- macOSキーチェーン統合
- password-storeによるパスワード管理
- GitHubプライベートリポジトリでのパスワード同期

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

既存のNixをクリーンアップするスクリプトを用意しています：

```bash
# クリーンアップスクリプトを実行
sudo ./cleanup_nix.sh

# macOSを再起動後、再度インストール
python3 bootstrap.py
```

### 手動でNixをインストールする場合

```bash
# 手動インストールスクリプトを実行
./manual_nix_install.sh
```

### 環境変数が読み込まれない場合

bootstrap.pyは自動的に環境変数を設定しますが、問題がある場合は：

```bash
# Nix環境変数を手動で読み込み
source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

### SSH鍵の問題

```bash
# SSH Agentの状態確認
ssh-add -l

# キーチェーンから再読み込み
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

### password-storeの使用方法

Bootstrap実行時に、GitHubプライベートリポジトリからpassword-storeをクローンできます。

```bash
# パスワードの一覧表示
pass

# パスワードの表示
pass show サービス名

# パスワードの生成（16文字）
pass generate サービス名 16

# パスワードをクリップボードにコピー（45秒後に自動削除）
pass show -c サービス名

# 変更をGitリポジトリにプッシュ
pass git push
```

便利なエイリアスも設定されています：
- `pw` - pass
- `pwg` - pass generate
- `pws` - pass show
- `pwc` - pass show -c（クリップボードにコピー）
- `pwgit` - pass git

## 📄 ライセンス

MIT License

## 🤝 貢献

プルリクエストを歓迎します！大きな変更の場合は、まずissueを作成して変更内容について議論してください。
