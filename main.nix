let
  tpl = { config, pkgs, lib, ... }:{
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

    # won't work on nixos yet
    programs.wireshark.enable = true; # installs setuid
    programs.wireshark.package = pkgs.tshark; # which one

    # TODO here we can set a custom initramfs/kernel
    # see my work on vagrant libvirt
    # <log file="/var/log/libvirt/qemu/guestname-serial0.log" append="off"/>
    # virsh + ttyconsole pour voir le numero
    deployment.libvirtd = {
      extraDevicesXML = ''
        <serial type='pty'>
        <target port='0'/>
        </serial>
        <console type='pty'>
        <target type='serial' port='0'/>
        </console>
      '';
      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # to see the botting message on the line
      cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0";
      # initrd = ""
      # todo set it to my local vmimage
      kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";
      # kernel=/tmp/vmlinux;
      # initrd=/tmp/vmlinux;
    };


    # TODO maybe add users
  };
in
rec {
  # network seems like a special attribute
  # the others are logical machines
  network.description = "Generate MPTCP pcap";
  server = tpl ;
  client = server;
}
