# { multihomed ? false , ... }:
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
        /home/teto/dotfiles/nixpkgs/common-all.nix
        /home/teto/dotfiles/nixpkgs/common-server.nix
        /home/teto/dotfiles/nixpkgs/modules/wireshark.nix
        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];


  boot.postBootCommands = ''
    ln -s /dev/sda1 /dev/root
  '';

  networking.firewall.enable = false;

  # mptcp-manual
  # boot.kernelPackages = pkgs.linuxPackages_mptcp-local;
  # boot.kernelPackages = pkgs.linuxPackagesFor pkgs.mptcp-manual;

  # WARNING: pick a kernel along the same version as tc ?
  # boot.kernelPackages = pkgs.linuxPackages_mptcp;
  # boot.blacklistedKernelModules = ["nouveau"];

  environment.systemPackages = with pkgs; [
    netperf
    tshark
    python
    # (python.withPackages(ps: with ps; [ mininet-python ] ))
  ];

  boot.kernelParams = [ "earlycon=ttyS0" "console=ttyS0" "boot.debug=1" "boot.consoleLogLevel=1" ];

  networking.mptcp.enable = true;

  networking.networkmanager = {
    enable=true;
    logLevel="DEBUG";
  };

  # IT MUST HAVE MININET !!
  programs.mininet = {
    enable = true;
  };

  # otherwise nix-shell won't work
  nix.nixPath = [
      # "nixos-unstable=https://github.com/nixos/nixpkgs-channels/archive/nixos-unstable.tar.gz"
      "nixpkgs=/root/nixpkgs"
      # "https://github.com/nixos/nixpkgs-channels/archive/nixos-18.03.tar.gz"
  ];

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
