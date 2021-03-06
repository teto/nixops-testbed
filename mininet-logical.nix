let
  tpl = { config, pkgs, lib,  ... }:
  let

    # myOverlay = /home/teto/dotfiles/nixpkgs/overlays/kernels.nix;
  in
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        # /home/teto/dotfiles/config/nixpkgs/overlays/kernels.nix
        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix

        # my test module
        # /home/teto/dotfiles/nixpkgs/modules/mptcp.nix

        # /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix
        # /home/teto/dotfiles/nixpkgs/config-all.nix
        # /home/teto/dotfiles/nixpkgs/servers/common-server.nix
        # /home/teto/dotfiles/nixpkgs/modules/wireshark.nix
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
  boot.kernelPackages = pkgs.linuxPackagesFor pkgs.mptcp9

  # WARNING: pick a kernel along the same version as tc ?
  # boot.kernelPackages = pkgs.linuxPackages_mptcp;
  # boot.blacklistedKernelModules = ["nouveau"];

  # (linuxPackagesFor pkgs.mptcp94-local-stable).bcc
  # mptcp94-local-stable.dev
  environment.systemPackages = with pkgs; [
    flent # https://flent.org/intro.html#quick-start
    gdb
    owamp
    ethtool # needed
    netperf
    tshark
    tcpdump
    python
    # will need to learn how to use it
    tmux
    webfs
    # (python.withPackages(ps: with ps; [ mininet-python ] ))
  ];

  boot.kernelParams = [ "earlycon=ttyS0" "console=ttyS0" "boot.debug=1" "boot.consoleLogLevel=1" ];


  # nixpkgs.overlays = let
  #   in lib.optionals (builtins.pathExists myOverlay)  [ (import myOverlay) ];

  networking.mptcp.enable = true;

  networking.networkmanager = {
    enable=true;
    logLevel="DEBUG";
  };

  # IT MUST HAVE MININET !!
  programs.mininet.enable = true;

  # see networkmanager.conf
  # [device]
  # match-device=interface-name:eth3
  # managed=1
  networking.networkmanager.unmanaged = [
    "interface-name:r?-*"
    "interface-name:r?-*"
    "interface-name:client-*"
    "interface-name:server-*"
    ];


  # system.stateVersion = "18.03";

  # owampd will run, then use owping to test
  # services.owamp.enable = true;

  # home-manager.users.teto = { ... }:
  # {
  #   imports = [
  #     # todo copy / paste ?
  #     /home/teto/dotfiles/nixpkgs/home-common.nix 
  #   ];
  # };


  # should match mininet configuration
  networking.extraHosts = ''
    7.7.7.7 server
  '';

  # when connecting as 
  # security.sudo.wheelNeedsPassword = lib.mkForce false;

  # extraFules allows
  # [ { commands = [ "ALL" ] ; groups = [ "sudo" ] ; } { commands = [ { command = "/home/root/secret.sh"; options = [ "SETENV" "NOPASSWD" ] ; } ] ; groups = [ 1006 ] ; users = [ "backup" "database" ] ; } { commands = [ "/home/baz/cmd1.sh hello-sudo"
           # { command = ''/home/baz/cmd2.sh ""''; options = [ "SETENV" ] ; } ] ; groups = [ "bar" ] ; runAs = "foo"; } ]
  nix = {
    # otherwise nix-shell won't work
    # nixPath = [
    # ];
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
