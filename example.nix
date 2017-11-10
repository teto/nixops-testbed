let
  tpl = { config, pkgs, lib, ... }:{
    imports = [
        /home/teto/dotfiles/nixpkgs/mptcp-kernel.nix
        /home/teto/dotfiles/nixpkgs/basetools.nix
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
    deployment.libvirtd.extraDevicesXML = ''
      <serial type='pty'>
        <target port='0'/>
      </serial>
      <console type='pty'>
        <target type='serial' port='0'/>
      </console>
    '';

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
