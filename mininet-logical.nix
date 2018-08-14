# { multihomed ? false , ... }:
# 
# mount -o remount,rw /nix/store
# chown -R root:root /nix/store
let
  tpl = { config, pkgs, lib,  ... }:
  let

    myOverlay = /home/teto/dotfiles/nixpkgs/overlays/kernels.nix;
  in
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        # /home/teto/dotfiles/config/nixpkgs/overlays/kernels.nix

        # my test module
        /home/teto/dotfiles/nixpkgs/modules/mptcp.nix

        /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix
        /home/teto/dotfiles/nixpkgs/config-all.nix
        /home/teto/dotfiles/nixpkgs/common-server.nix
        /home/teto/dotfiles/nixpkgs/modules/wireshark.nix
        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];


  boot.postBootCommands = ''
    # after first deploy
    ln -s /dev/sda1 /dev/root

    # eventually to work around https://github.com/NixOS/nixops/issues/931#issuecomment-385662909
    mount -o remount,rw /nix/store
    chown -R root:root /nix/store
  '';

  networking.firewall.enable = false;

  # mptcp-manual
  # boot.kernelPackages = pkgs.linuxPackages_mptcp-local;
  boot.kernelPackages = pkgs.linuxPackagesFor pkgs.mptcp-local-stable;

  # WARNING: pick a kernel along the same version as tc ?
  # boot.kernelPackages = pkgs.linuxPackages_mptcp;
  # boot.blacklistedKernelModules = ["nouveau"];

  environment.systemPackages = with pkgs; [
    flent # https://flent.org/intro.html#quick-start
    owamp
    ethtool # needed
    netperf
    tshark
    home-manager
    tcpdump
    python
    (linuxPackagesFor pkgs.mptcp-local-stable).bcc
    mptcp-local-stable.dev
    # will need to learn how to use it
    tmux
    # (python.withPackages(ps: with ps; [ mininet-python ] ))
  ];

  boot.kernelParams = [ "earlycon=ttyS0" "console=ttyS0" "boot.debug=1" "boot.consoleLogLevel=1" ];


  nixpkgs.overlays = let
    myOverlay = /home/teto/dotfiles/nixpkgs/overlays/kernels.nix;
    in lib.optionals (builtins.pathExists myOverlay)  [ (import myOverlay) ];

  networking.mptcp.enable = true;

  networking.networkmanager = {
    enable=true;
    logLevel="DEBUG";
  };

  # IT MUST HAVE MININET !!
  programs.mininet = {
    enable = true;
  };

  system.nixos.stateVersion = "18.03";

  services.owamp.enable = true;

  home-manager.users.teto = { ... }:
  {
    imports = [
      /home/teto/dotfiles/nixpkgs/home-common.nix 
    ];
  };

  # when connecting as 
  security.sudo.wheelNeedsPassword = false;

  # extraFules allows
  # [ { commands = [ "ALL" ] ; groups = [ "sudo" ] ; } { commands = [ { command = "/home/root/secret.sh"; options = [ "SETENV" "NOPASSWD" ] ; } ] ; groups = [ 1006 ] ; users = [ "backup" "database" ] ; } { commands = [ "/home/baz/cmd1.sh hello-sudo"
           # { command = ''/home/baz/cmd2.sh ""''; options = [ "SETENV" ] ; } ] ; groups = [ "bar" ] ; runAs = "foo"; } ]
  nix = {
  # otherwise nix-shell won't work
    nixPath = [
          # "nixos-unstable=https://github.com/nixos/nixpkgs-channels/archive/nixos-unstable.tar.gz"
          "nixpkgs=/home/teto/nixpkgs"
          # "nixpkgs-overlays=/home/teto/dotfiles/nixpkgs/overlays"
          # "https://github.com/nixos/nixpkgs-channels/archive/nixos-18.03.tar.gz"
    ];

    # would be better with a dns name
    # so that we can download from
    binaryCaches =  [ "http://192.168.128.1:8080" ];
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
