# after deployement run
# nixops ssh-for-each "ln -s /dev/sda1 /dev/root"
{ multihomed ? false , ... }:
let
  tpl = { config, pkgs, lib,  ... }:
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix
        /home/teto/dotfiles/nixpkgs/common-all.nix
        /home/teto/dotfiles/nixpkgs/common-server.nix
        /home/teto/dotfiles/nixpkgs/modules/wireshark.nix
        # for now don't use it
        /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];

    boot.kernelParams = [ "earlycon=ttyS0" "console=ttyS0" "boot.debug=1" "boot.consoleLogLevel=1" ];

    # nixpkgs.overlays = [ (import ./overlays/this.nix) (import ./overlays/that.nix) ]
    # nixpkgs.overlays = [
    #   (import /home/teto/dotfiles/config/nixpkgs/overlays/i3.nix)
    # ];

    # TODO run commands on boot

    # TODO use webfs instead ?
    # services.httpd.enable = true;
    # services.httpd.adminAddr = "alice@example.org";
    # services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    # networking.firewall.enable = false;

    # just trying
    networking.dnsExtensionMechanism = false;
    networking.dnsSingleRequest = false;

    # allowedTCPPorts = [ 80 ];
    # networking.networkmanager = {
    #   enable=true;
    # #   # one of "dhclient", "dhcpcd", "internal"
    # #   dhcp="dhcpcd";
    # #   # networking.networkmanager.useDnsmasq
    # # #   enableStrongSwan = true;
    # # #   # one of "OFF", "ERR", "WARN", "INFO", "DEBUG", "TRACE"
    # # #   logLevel="DEBUG";
    # # #   wifi.scanRandMacAddress = true;
    # };

    # contradicts networkmanager
    # networking.useDHCP = true;

    # boot.postBootCommands = ''
    #   ln -s /dev/sda1 /dev/root
    # '';

    environment.systemPackages = with pkgs; [
      at # to run in background
      ethtool # to check for segmentation offload
      tmux   # to have it survive ssh closing, nohup can help too
      iperf
      # iperf2
      netperf
      # tshark
    ];

    # TODO here we can set a custom initramfs/kernel
    # see my work on vagrant libvirt
    # <log file="/var/log/libvirt/qemu/guestname-serial0.log" append="off"/>
    # virsh + ttyconsole pour voir le numero
    # TODO maybe add users

  } 
  );


  # client_tpl = {config, pkgs, ... } @ args:
  # (tpl args);
  # // {
    # need to be multihomed
    # networking.interfaces = {
    #   eth0 = { name = "eth0"; useDHCP=true; };
    #   # eth1 = { name = "eth1"; useDHCP=true; };
    # };

    # networking.firewall.enable = false;
    # # to execute at the end of a setupped network
    # # networking.localCommands=
  # };
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
