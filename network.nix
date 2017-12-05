let
  tpl = { config, pkgs, lib, ... }:
  {
    imports = [
      # Not needed if we use the libvirt kernel interface
        # /home/teto/dotfiles/nixpkgs/mptcp-kernel.nix
        /home/teto/dotfiles/nixpkgs/basetools.nix
      # nixpkgs.overlays = [ (import ./overlays/this.nix) (import ./overlays/that.nix) ]
      ];

    nixpkgs.overlays = [
      (import /home/teto/dotfiles/config/nixpkgs/overlays/i3.nix)
    ];

    # TODO run commands on boot

    # TODO use webfs instead ?
    # services.httpd.enable = true;
    # services.httpd.adminAddr = "alice@example.org";
    # services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    networking.firewall.enable = false;
    # allowedTCPPorts = [ 80 ];

    # TODO have it export TERM
    environment.systemPackages = with pkgs; [
      at # to run in background
      tmux   # to have it survive ssh closing, nohup can help too
      iperf
      iperf2
      netperf
      tshark
    ];
    programs.bash.enableCompletion = true;
    programs.bash.shellInit = ''
      export TERM=linux;
      '';

    # services.openssh = {
    #   permitRootLogin = "no";
    #   passwordAuthentication = false;
    #   # enable = false;
    # };

    # won't work on nixos yet
    programs.wireshark.enable = true; # installs setuid
    programs.wireshark.package = pkgs.tshark; # which one

    # TODO here we can set a custom initramfs/kernel
    # see my work on vagrant libvirt
    # <log file="/var/log/libvirt/qemu/guestname-serial0.log" append="off"/>
    # virsh + ttyconsole pour voir le numero
    # TODO maybe add users
    users.extraUsers.teto = {
      isNormalUser = true; # creates home/ sets default shell
      uid = 1000;
      extraGroups = [
        "audio" # for pulseaudio 
        "wheel" # for sudo
        "networkmanager"
        "libvirtd" # for nixops
        "adbusers" # for android tools
        "wireshark"
        "plugdev" # for udiskie
        # "kvm" # don't think that's needed
      ];
      # once can set initialHashedPassword too
      initialPassword = "teto";
      # shell = pkgs.zsh;
      # TODO import it from desktopPkgs for instance ?
      # packages = [
      #   pkgs.termite pkgs.sxiv
      # ];
    };

    # prints everything superior to this number
    boot.consoleLogLevel=1;

  };
in
rec {
  # network seems like a special attribute
  # the others are logical machines
  network.description = "Generate MPTCP pcap";
  server = tpl ;
  # client = server;
}
