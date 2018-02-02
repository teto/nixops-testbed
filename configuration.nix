
# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running ‘nixos-help’).

{ config, pkgs, lib, ... }:
let
  userNixpkgs = /home/teto/nixpkgs;
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

  networking.hostName = "matt_vm"; # Define your hostname.
  networking.defaultGateway = "202.214.86.1";
  networking.nameservers = ["210.130.207.46"];
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
     fd
     termite # for the TERMINFO
     vim
     neovim
     weechat
     tmux
     iperf
     nixUnstable
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

  # Next we have to make sure our user has access to create images by executing:
  # $ sudo mkdir /var/lib/libvirt/images
  # $ sudo chgrp libvirtd /var/lib/libvirt/images
  # $ sudo chmod g+w /var/lib/libvirt/images

  # systemd.services.libvirtd.restartIfChanged = lib.mkForce true;


  # Enable the OpenSSH daemon.
  services.openssh = {
          enable = true;
          permitRootLogin = "no";
        passwordAuthentication = false;
        challengeResponseAuthentication = false;
  };

  # This value determines the NixOS release with which your system is to be
  # compatible, in order to avoid breaking some software such as database
  # servers. You should change this only after NixOS release notes say you
  # should.
  system.stateVersion = "17.09"; # Did you read the comment?
  nix = {
    # buildCores=4;
    nixPath = [
      "nixos-config=/home/teto/testbed/configuration.nix"
      "/nix/var/nix/profiles/per-user/root/channels"
    ]
    ++ lib.optionals (builtins.pathExists userNixpkgs)  [ "nixpkgs=${builtins.toString userNixpkgs}" ]
    ;
    #  to keep build-time dependencies around => rebuild while being offline
    # build-use-sandbox = true
    extraOptions = ''
      # careful will prevent from fetching local git !
      # build-use-sandbox = true
      gc-keep-outputs = true
      gc-keep-derivations = true
    '';

    # either use --option extra-binary-caches http://hydra.nixos.org/
    # nix.binaryCaches = [ http://hydra.nixos.org/ ];
    # handy to hack/fix around
    readOnlyStore = false;
  };
}

