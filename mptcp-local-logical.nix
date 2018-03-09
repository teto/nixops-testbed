let
  tpl = { config, pkgs, lib, ... }:
  {
    # prints everything superior to this number

    imports = [
      # Not needed if we use the libvirt kernel interface
        /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix
        /home/teto/dotfiles/nixpkgs/common.nix
        /home/teto/dotfiles/nixpkgs/wireshark.nix
      ];

    # nixpkgs.overlays = [ (import ./overlays/this.nix) (import ./overlays/that.nix) ]
    # nixpkgs.overlays = [
    #   (import /home/teto/dotfiles/config/nixpkgs/overlays/i3.nix)
    # ];

    # TODO run commands on boot

    # TODO use webfs instead ?
    # services.httpd.enable = true;
    # services.httpd.adminAddr = "alice@example.org";
    # services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    networking.firewall.enable = false;
    # allowedTCPPorts = [ 80 ];
    
    boot.postBootCommands = ''
      ln -s /dev/sda1 /dev/root
    '';

    environment.systemPackages = with pkgs; [
      at # to run in background
      tmux   # to have it survive ssh closing, nohup can help too
      iperf
      iperf2
      netperf
      tshark
    ];

    # TODO here we can set a custom initramfs/kernel
    # see my work on vagrant libvirt
    # <log file="/var/log/libvirt/qemu/guestname-serial0.log" append="off"/>
    # virsh + ttyconsole pour voir le numero
    # TODO maybe add users

  };
in
rec {
  # network seems like a special attribute
  # the others are logical machines
  network = {
    description = "local MPTCP";
    enableRollback = false;
  };

  # server = tpl ;
  # <custom/>
  # server = import /home/teto/dotfiles/nixpkgs/config-iij-mptcp.nix;
  server = tpl;
  client = tpl;
}
