"""
システム設定を検出してNix設定を生成するモジュール
"""

import subprocess
import plistlib
import logging
from pathlib import Path
import json
import yaml


class SystemConfigDetector:
    """現在のmacOS設定を読み取り、Nix設定を生成するクラス"""
    
    def __init__(self, logger):
        self.logger = logger
        self.config_dir = Path.home() / '.config/nix-darwin'
        self.templates_dir = Path(__file__).parent.parent / 'templates'
        
    def read_current_dock_settings(self):
        """現在のDock設定を読み取り"""
        self.logger.info("Dock設定を読み取り中...")
        
        dock_settings = {}
        
        # defaultsコマンドで設定を読み取り
        dock_keys = {
            'autohide': 'com.apple.dock autohide',
            'autohide-delay': 'com.apple.dock autohide-delay',
            'autohide-time-modifier': 'com.apple.dock autohide-time-modifier',
            'tilesize': 'com.apple.dock tilesize',
            'orientation': 'com.apple.dock orientation',
            'show-recents': 'com.apple.dock show-recents',
            'static-only': 'com.apple.dock static-only',
            'mineffect': 'com.apple.dock mineffect'
        }
        
        for key, defaults_key in dock_keys.items():
            try:
                result = subprocess.run(
                    ['defaults', 'read'] + defaults_key.split(),
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    value = result.stdout.strip()
                    # 数値変換を試みる
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        # 文字列のまま
                        if value == '1':
                            value = True
                        elif value == '0':
                            value = False
                            
                    dock_settings[key.replace('-', '_')] = value
                    
            except Exception as e:
                self.logger.debug(f"Dock設定 {key} の読み取りエラー: {e}")
                
        self.logger.info(f"Dock設定を取得: {len(dock_settings)}項目")
        return dock_settings
        
    def read_current_finder_settings(self):
        """現在のFinder設定を読み取り"""
        self.logger.info("Finder設定を読み取り中...")
        
        finder_settings = {}
        
        finder_keys = {
            'AppleShowAllFiles': 'com.apple.finder AppleShowAllFiles',
            'ShowStatusBar': 'com.apple.finder ShowStatusBar',
            'ShowPathbar': 'com.apple.finder ShowPathbar',
            'FXDefaultSearchScope': 'com.apple.finder FXDefaultSearchScope',
            'FXPreferredViewStyle': 'com.apple.finder FXPreferredViewStyle'
        }
        
        for key, defaults_key in finder_keys.items():
            try:
                result = subprocess.run(
                    ['defaults', 'read'] + defaults_key.split(),
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    value = result.stdout.strip()
                    if value == 'YES' or value == '1':
                        value = True
                    elif value == 'NO' or value == '0':
                        value = False
                        
                    finder_settings[key] = value
                    
            except Exception as e:
                self.logger.debug(f"Finder設定 {key} の読み取りエラー: {e}")
                
        self.logger.info(f"Finder設定を取得: {len(finder_settings)}項目")
        return finder_settings
        
    def read_current_system_settings(self):
        """現在のシステム設定を読み取り"""
        self.logger.info("システム設定を読み取り中...")
        
        system_settings = {}
        
        system_keys = {
            'AppleShowAllExtensions': 'NSGlobalDomain AppleShowAllExtensions',
            'ApplePressAndHoldEnabled': 'NSGlobalDomain ApplePressAndHoldEnabled',
            'KeyRepeat': 'NSGlobalDomain KeyRepeat',
            'InitialKeyRepeat': 'NSGlobalDomain InitialKeyRepeat',
            'AppleInterfaceStyle': 'NSGlobalDomain AppleInterfaceStyle'
        }
        
        for key, defaults_key in system_keys.items():
            try:
                result = subprocess.run(
                    ['defaults', 'read'] + defaults_key.split(),
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    value = result.stdout.strip()
                    try:
                        value = int(value)
                    except ValueError:
                        if value == 'YES' or value == '1':
                            value = True
                        elif value == 'NO' or value == '0':
                            value = False
                            
                    system_settings[key] = value
                    
            except Exception as e:
                self.logger.debug(f"システム設定 {key} の読み取りエラー: {e}")
                
        self.logger.info(f"システム設定を取得: {len(system_settings)}項目")
        return system_settings
        
    def generate_nix_config(self):
        """現在の設定からNix設定を生成"""
        self.logger.info("Nix設定を生成中...")
        
        # 設定ディレクトリの作成
        self.config_dir.mkdir(parents=True, exist_ok=True)
        modules_dir = self.config_dir / 'modules'
        modules_dir.mkdir(exist_ok=True)
        
        # 現在の設定を読み取り
        dock_settings = self.read_current_dock_settings()
        finder_settings = self.read_current_finder_settings()
        system_settings = self.read_current_system_settings()
        
        # flake.nixの生成
        self._generate_flake_nix()
        
        # darwin-configuration.nixの生成
        self._generate_darwin_configuration()
        
        # home.nixの生成
        self._generate_home_nix()
        
        # モジュールの生成
        self._generate_system_module(dock_settings, finder_settings, system_settings)
        self._generate_packages_module()
        self._generate_homebrew_module()
        
        self.logger.info("✅ Nix設定の生成が完了しました")
        
    def _generate_flake_nix(self):
        """flake.nixを生成"""
        # Get hostname and username
        hostname = subprocess.run(
            ['hostname', '-s'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        username = subprocess.run(
            ['whoami'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        flake_content = f'''{{
  description = "nix-darwin system configuration";

  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin = {{
      url = "github:LnL7/nix-darwin";
      inputs.nixpkgs.follows = "nixpkgs";
    }};
    home-manager = {{
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    }};
  }};

  outputs = inputs@{{ self, nix-darwin, nixpkgs, home-manager }}: {{
    darwinConfigurations."{hostname}" = nix-darwin.lib.darwinSystem {{
      system = "aarch64-darwin";  # Apple Silicon
      
      modules = [
        ./darwin-configuration.nix
        home-manager.darwinModules.home-manager
        {{
          home-manager.useGlobalPkgs = true;
          home-manager.useUserPackages = true;
          home-manager.users.{username} = import ./home.nix;
        }}
      ];
    }};

    # Convenience output for applying the configuration
    darwinPackages = self.darwinConfigurations."{hostname}".pkgs;
  }};
}}
'''
        
        flake_path = self.config_dir / 'flake.nix'
        flake_path.write_text(flake_content)
        self.logger.info(f"生成: {flake_path}")
        
    def _generate_darwin_configuration(self):
        """darwin-configuration.nixを生成"""
        username = subprocess.run(
            ['whoami'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        config_content = f"""{{ config, pkgs, ... }}:

{{
  # Import modules
  imports = [
    ./modules/system.nix
    ./modules/packages.nix
    ./modules/homebrew.nix
  ];

  # Nix settings
  
  # Enable experimental features
  nix.settings = {{
    experimental-features = "nix-command flakes";
    trusted-users = [ "root" "{username}" ];
  }};

  # Create /etc/zshrc that loads the nix-darwin environment
  programs.zsh.enable = true;
  
  # Set Git commit hash for darwin-version (optional)
  # system.configurationRevision = self.rev or self.dirtyRev or null;

  # Used for backwards compatibility
  system.stateVersion = 4;

  # Set primary user for nix-darwin
  system.primaryUser = "{username}";

  # The user configuration
  users.users.{username} = {{
    name = "{username}";
    home = "/Users/{username}";
  }};
  
  # Allow unfree packages
  nixpkgs.config.allowUnfree = true;
}}
"""
        
        config_path = self.config_dir / 'darwin-configuration.nix'
        config_path.write_text(config_content)
        self.logger.info(f"生成: {config_path}")
        
    def _generate_home_nix(self):
        """home.nixを生成"""
        home_content = """{ config, pkgs, ... }:

{
  # Home Manager needs a bit of information about you and the
  # paths it should manage
  home.stateVersion = "23.11";

  # Let Home Manager install and manage itself
  programs.home-manager.enable = true;

  # Git configuration
  programs.git = {
    enable = true;
    extraConfig = {
      init.defaultBranch = "main";
      pull.rebase = false;
      push.autoSetupRemote = true;
    };
  };

  # Zsh configuration
  programs.zsh = {
    enable = true;
    enableAutosuggestions = true;
    enableCompletion = true;
    syntaxHighlighting.enable = true;
    
    oh-my-zsh = {
      enable = true;
      theme = "robbyrussell";
      plugins = [ "git" "docker" "kubectl" ];
    };
    
    shellAliases = {
      ll = "ls -la";
      gc = "git commit";
      gp = "git push";
      gs = "git status";
      rebuild = "darwin-rebuild switch --flake ~/.config/nix-darwin";
      
      # password-store aliases
      pw = "pass";
      pwg = "pass generate";
      pws = "pass show";
      pwf = "pass find";
      pwc = "pass show -c";
      pwgit = "pass git";
    };
  };

  # VS Code configuration
  programs.vscode = {
    enable = true;
    extensions = with pkgs.vscode-extensions; [
      ms-python.python
      ms-vscode.cpptools
      jnoortheen.nix-ide
      github.copilot
    ];
  };
}
"""
        
        home_path = self.config_dir / 'home.nix'
        home_path.write_text(home_content)
        self.logger.info(f"生成: {home_path}")
        
    def _generate_system_module(self, dock_settings, finder_settings, system_settings):
        """system.nixモジュールを生成"""
        # Nix形式に変換
        def to_nix_value(value):
            if isinstance(value, bool):
                return 'true' if value else 'false'
            elif isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, (int, float)):
                return str(value)
            else:
                return f'"{str(value)}"'
                
        # Dock設定の文字列生成
        dock_lines = []
        for key, value in dock_settings.items():
            dock_lines.append(f'    {key} = {to_nix_value(value)};')
            
        # Finder設定の文字列生成
        finder_lines = []
        for key, value in finder_settings.items():
            finder_lines.append(f'    {key} = {to_nix_value(value)};')
            
        # システム設定の文字列生成
        system_lines = []
        for key, value in system_settings.items():
            system_lines.append(f'    {key} = {to_nix_value(value)};')
            
        system_content = f"""{{ config, pkgs, ... }}:

{{
  # macOS system defaults
  system.defaults = {{
    # Dock configuration
    dock = {{
{chr(10).join(dock_lines)}
    }};
    
    # Finder configuration
    finder = {{
{chr(10).join(finder_lines)}
    }};
    
    # Global system settings
    NSGlobalDomain = {{
{chr(10).join(system_lines)}
    }};
    
    # Screenshot settings
    screencapture = {{
      location = "~/Desktop";
      type = "png";
    }};
  }};
  
  # Enable Touch ID for sudo
  security.pam.services.sudo_local.touchIdAuth = true;
}}
"""
        
        system_path = self.config_dir / 'modules' / 'system.nix'
        system_path.write_text(system_content)
        self.logger.info(f"生成: {system_path}")
        
    def _generate_packages_module(self):
        """packages.nixモジュールを生成"""
        packages_content = """{ config, pkgs, ... }:

{
  # System packages
  environment.systemPackages = with pkgs; [
    # Version control
    git
    gh
    
    # Development tools
    vim
    neovim
    tmux
    direnv
    
    # System tools
    curl
    wget
    htop
    tree
    jq
    ripgrep
    fd
    bat
    eza
    
    # Container tools
    colima
    docker-client
    docker-compose
    
    # Node.js development
    nodejs_20
    yarn
    
    # Python development
    python311
    python311Packages.pip
    
    # Nix tools
    nil
    nixpkgs-fmt
    nix-tree
    
    # Password management
    pass
    gnupg
    pinentry_mac
  ];
}
"""
        
        packages_path = self.config_dir / 'modules' / 'packages.nix'
        packages_path.write_text(packages_content)
        self.logger.info(f"生成: {packages_path}")
        
    def _generate_homebrew_module(self):
        """homebrew.nixモジュールを生成"""
        homebrew_content = """{ config, pkgs, ... }:

{
  # Homebrew configuration
  homebrew = {
    enable = true;
    
    # Automatically update Homebrew and upgrade packages
    onActivation = {
      autoUpdate = true;
      upgrade = true;
      cleanup = "zap";
    };
    
    # Taps
    taps = [
      "homebrew/cask"
      "homebrew/cask-versions"
    ];
    
    # Homebrew packages (for things not in nixpkgs)
    brews = [
      # Add any brew formulas here
    ];
    
    # Cask applications
    casks = [
      # Terminal
      "warp"
      
      # Productivity
      "raycast"
      "notion"
      
      # Browsers
      "firefox-developer-edition"
      "google-chrome"
      
      # Development
      "visual-studio-code"
      "docker"
      
      # Communication
      "slack"
      "discord"
      
      # Utilities
      "rectangle"
    ];
    
    # Mac App Store apps
    masApps = {
      # "App Name" = App ID;
    };
  };
}
"""
        
        homebrew_path = self.config_dir / 'modules' / 'homebrew.nix'
        homebrew_path.write_text(homebrew_content)
        self.logger.info(f"生成: {homebrew_path}")
        
    def save_current_settings(self, output_file=None):
        """現在の設定をYAMLファイルに保存"""
        if not output_file:
            output_file = self.config_dir / 'current-settings.yaml'
            
        self.logger.info(f"現在の設定を保存中: {output_file}")
        
        settings = {
            'dock': self.read_current_dock_settings(),
            'finder': self.read_current_finder_settings(),
            'system': self.read_current_system_settings()
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False)
            
        self.logger.info("✅ 設定の保存が完了しました")
