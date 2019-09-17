# { multihomed ? false , ... }:
# 
# mount -o remount,rw /nix/store
# chown -R root:root /nix/store
let
  tpl = { config, pkgs, lib,  ... }:
  let
    myKernel = pkgs.linux_mptcp_trunk_raw;
    # myKernel = pkgs.linux_mptcp;
    dotfiles = /home/teto/dotfiles;
    myOverlay = dotfiles + /config/nixpkgs/overlays/kernels.nix;
  in
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        # /home/teto/dotfiles/config/nixpkgs/overlays/kernels.nix

        # my test module
        # /home/teto/dotfiles/nixpkgs/modules/mptcp.nix

        # /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix

        # /home/teto/dotfiles/nixpkgs/config-all.nix
        /home/teto/dotfiles/nixpkgs/servers/common-server.nix
        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];

  programs.wireshark.enable = true; # installs setuid
  programs.wireshark.package = pkgs.tshark; # which one

  # eventually to work around https://github.com/NixOS/nixops/issues/931#issuecomment-385662909
  # mount -o remount,rw /nix/store
  # chown -R root:root /nix/store

  # TODO I should use labels instead ? so that it remains consistent between
  # buses (IDE/VIRTIO)
  # system.activationScripts.createDevRoot = ''
  #   # if does not exist ?!
  #   ln -s /dev/vda1 /dev/root
  # '';

    # boot.kernelModules
    #     boot.initrd.availableKernelModules or boot.initrd.kernelModules.


  boot.postBootCommands = ''
    # after first deploy
    ln -s /dev/vda1 /dev/root

  '';

  boot.consoleLogLevel=8;

  # Look at http://multipath-tcp.org/pmwiki.php/Users/ConfigureMPTCP
  boot.kernel.sysctl = {
    # https://lwn.net/Articles/542642/
    "net.ipv4.tcp_early_retrans" = 3;

    # VERY IMPORTANT to disable syncookies since it will change the timestamp
    "net.ipv4.tcp_syncookies" = 0;

    # seems to generate problems when connecting via ssh; for now disable it
    "net.ipv4.tcp_timestamps" = 0;

    "net.mptcp.mptcp_checksum" = 0;
    "net.mptcp.mptcp_enabled" = 0;
  };

  system.activationScripts.nixops-vm-fix-931 = ''
    if ls -l /nix/store | grep sudo | grep -q nogroup; then
      mount -o remount,rw  /nix/store
      chown -R root:nixbld /nix/store
    fi
  '';

  # services.qemuGuest.enable = true;

  # Just in my branch for now
  services.openssh.banner = "Hello Matt";


  # environment.etc."motd" = 


  # TODO let's ignore mininet for now
  # networking.useDHCP = true;

  #
  security.sudo.wheelNeedsPassword = false;

  networking.firewall.enable = false;


  # mptcp-manual
  # boot.kernelPackages = pkgs.linuxPackages_mptcp-local;
  # boot.kernelPackages = pkgs.linuxPackagesFor pkgs.mptcp94-local-stable;
  # boot.kernelPackages = pkgs.linuxPackagesFor pkgs.linux;

  # WARNING: pick a kernel along the same version as tc ?
  # boot.kernelPackages = pkgs.linuxPackages_mptcp;
  # boot.blacklistedKernelModules = ["nouveau"];

  environment.systemPackages = with pkgs; [
    # flent # https://flent.org/intro.html#quick-start
    # gdb
    owamp # use module instead ?
    ethtool # needed
    # netperf
    # tshark
    home-manager
    tcpdump
    python
    # will need to learn how to use it
    tmux
    webfs
    # (python.withPackages(ps: with ps; [ mininet-python ] ))

    # find some ways to move it to networking.mptcp
    # c ca qui foire
    # iproute_mptcp
  ]
  # enable if we use bcc, or just mount it !
  # ++ lib.optionals false [
  #   (linuxPackagesFor myKernel).bcc
  #   myKernel.dev
  # ]
  ;

  # similar to the physical config when passing
  # pass root as well
  boot.kernelParams = [
    "earlycon=ttyS0"
    "console=ttyS0"
    "boot.debug=1"
    # "boot.consoleLogLevel=1"
    "raid=noautodetect"
    "root=/dev/vda1"
  ];

  # for use in libvirt
  boot.initrd.availableKernelModules = [ "ext4" ];

  nixpkgs.overlays = lib.optionals (builtins.pathExists myOverlay)  [ (import myOverlay) ];

  # networking.mptcp = {
  #   enable = false;
  #   debug = true;
  #   # TODO set it during the experiments only
  #   # pathManager = "netlink";
  #   # package = pkgs.linux_mptcp_trunk_raw;
  #   package = myKernel;
  # };


  # plays badly
  networking.networkmanager = {
    enable=true;
    logLevel="DEBUG";

    # device specific configuration
    # https://developer.gnome.org/NetworkManager/1.18/NetworkManager.conf.html
    unmanaged = [
      "interface-name:r?-*"
      "interface-name:gateway-*"
      # "except-interface:"
      "interface-name:client-*"
      "interface-name:server-*"
    ];
    # see networkmanager.conf
    # extraConfig = ''
    # [device]
    # match-device=interface-name:client-*
    # managed=1
    # # ignore-carrier
    # '';
    # to prevent networkmanager from interfering with the mininet configuration
    # what kind of error did trigger that ?
    # dns = "none";
  };

  programs.mininet.enable = true;



  # owampd will run, then use owping to test
  # services.owamp.enable = true;

  home-manager.users.teto = { ... }:
  {
    imports = [
      /home/teto/dotfiles/nixpkgs/home-common.nix
    ];
  };


  # should match mininet configuration
  # networking.extraHosts = ''
  #   7.7.7.7 server
  # '';

  # when connecting as 
  # security.sudo.wheelNeedsPassword = lib.mkForce false;

  # extraFules allows
  # [ { commands = [ "ALL" ] ; groups = [ "sudo" ] ; } { commands = [ { command = "/home/root/secret.sh"; options = [ "SETENV" "NOPASSWD" ] ; } ] ; groups = [ 1006 ] ; users = [ "backup" "database" ] ; } { commands = [ "/home/baz/cmd1.sh hello-sudo"
           # { command = ''/home/baz/cmd2.sh ""''; options = [ "SETENV" ] ; } ] ; groups = [ "bar" ] ; runAs = "foo"; } ]
  nix = {
  # otherwise nix-shell won't work

  # options.nix.nixPath.default 
    nixPath = [
          # "nixos-unstable=https://github.com/nixos/nixpkgs-channels/archive/nixos-unstable.tar.gz"
          "nixpkgs=/home/teto/nixpkgs"
          # "nixpkgs-overlays=/home/teto/dotfiles/nixpkgs/overlays"
          # "https://github.com/nixos/nixpkgs-channels/archive/nixos-18.03.tar.gz"
    ];

    # would be better with a dns name
    # so that we can download from
    # Look at the value of the defualt network (virbr1 most likely)
    binaryCaches =  [ "http://192.168.122.1:8080" ];
    requireSignedBinaryCaches = false;

  };
});
in
rec {

  network = {
    description = "mininet MPTCP VM";
    enableRollback = false;
  };

  main = tpl;
  # or inherit main
}
