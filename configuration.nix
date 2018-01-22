
# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running ‘nixos-help’).

{ config, pkgs, ... }:
let
        gitolitePublicKey =  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDmt8RlXKAn7zryenWl8e8RDLZ+WLzIsdqwDMbvynF/Eg3zraxWpm80cXlIrGAayHf8eTjmWXoDnWBuS3MHjv9nTWHliJVyHC5/aImrGflkGpWWpBvxg79bIz06QusqBx4Vfq6NKn/GS6L8KevhtMToLmEOyRuB3Gs1FWsHb/EbqKp5hzDYS3yVMjVkF+cubQiK/DEvcio/G/vSDrBcPE8kUZcf3ibsBruUa3tCh4RTmaLnoIbkOX/ColTWPIOhMlnYeOOzZ22ln6cgBgarjU/DEpb4iu0qSjTArNV58mUpqzEUU0sTq2sunK0hdEDkxWw/3qpv6MI276AQ4QrY2wTN";
in
{
  imports =
    [ # Include the results of the hardware scan.
      /etc/nixos/hardware-configuration.nix
    ];

  # Use the GRUB 2 boot loader.
  boot.loader.grub.enable = true;
  boot.loader.grub.version = 2;
  # boot.loader.grub.efiSupport = true;
  # boot.loader.grub.efiInstallAsRemovable = true;
  # boot.loader.efi.efiSysMountPoint = "/boot/efi";
  # Define on which hard drive you want to install Grub.
  boot.loader.grub.device = "/dev/sda"; # or "nodev" for efi only

  networking.hostName = "nixos_git"; # Define your hostname.
  networking.defaultGateway = "202.214.86.1";
  networking.nameservers = ["210.130.207.46"];
  networking.interfaces.ens3.ip4 = [ { address = "202.214.86.52"; prefixLength = 25; }];
  # networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.

  # Select internationalisation properties.
  # i18n = {
  #   consoleFont = "Lat2-Terminus16";
  #   consoleKeyMap = "us";
  #   defaultLocale = "en_US.UTF-8";
  # };

  # Set your time zone.
  # time.timeZone = "Europe/Amsterdam";

  # List packages installed in system profile. To search by name, run:
  # $ nix-env -qaP | grep wget
   environment.systemPackages = with pkgs; [
     wget
     termite # for the TERMINFO ?
     vim
        neovim
        weechat
        tmux
        iperf
   ];

  # Some programs need SUID wrappers, can be configured further or are
  # started in user sessions.
  programs.bash.enableCompletion = true;

  # programs.mtr.enable = true;
  # programs.gnupg.agent = { enable = true; enableSSHSupport = true; };

  # List services that you want to enable:


  # Open ports in the firewall.
  # networking.firewall.allowedTCPPorts = [ ... ];
  # networking.firewall.allowedUDPPorts = [ ... ];
  # Or disable the firewall altogether.
  # networking.firewall.enable = false;

  # Enable CUPS to print documents.
  # services.printing.enable = true;

  # Enable the X11 windowing system.
  # services.xserver.enable = true;
  # services.xserver.layout = "us";
  # services.xserver.xkbOptions = "eurosign:e";

  # Enable touchpad support.
  # services.xserver.libinput.enable = true;

  # Enable the KDE Desktop Environment.
  # services.xserver.displayManager.sddm.enable = true;
  # services.xserver.desktopManager.plasma5.enable = true;
  virtualisation.libvirtd = {
    enable = true;
    qemuVerbatimConfig = ''
      namespaces = []

      # Whether libvirt should dynamically change file ownership
      dynamic_ownership = 1
      # be careful for network teto might make if fail
      user="teto"
      group="libvirtd"
      '';
  };
  # systemd.services.libvirtd.restartIfChanged = lib.mkForce true;

  # Define a user account. Don't forget to set a password with ‘passwd’.
  users.extraUsers.teto = {
    isNormalUser = true;
    description = "matt";
    extraGroups = [ "wheel" "networkmanager" "libvirtd"];
    openssh.authorizedKeys.keys = [ gitolitePublicKey ];
    uid = 1000;
  };

  # Enable the OpenSSH daemon.
  services.openssh = {
          enable = true;
          permitRootLogin = "no";
        passwordAuthentication = false;
        challengeResponseAuthentication = false;
  };

  # enable gitolite
  services.gitolite = {
        enable = true;
        adminPubkey = gitolitePublicKey ;
  };

  # This value determines the NixOS release with which your system is to be
  # compatible, in order to avoid breaking some software such as database
  # servers. You should change this only after NixOS release notes say you
  # should.
  system.stateVersion = "17.09"; # Did you read the comment?

}

