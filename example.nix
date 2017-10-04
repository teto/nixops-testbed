{
  network.description = "toto";
  example = { config, pkgs, lib, ... }:
  {
    imports = [
        /home/teto/dotfiles/nixpkgs/mptcp-kernel.nix
        /home/teto/dotfiles/nixpkgs/basetools.nix
      ];

    # TODO run commands on boot

    # TODO use webfs instead ?
    services.httpd.enable = true;
    services.httpd.adminAddr = "alice@example.org";
    services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    networking.firewall.allowedTCPPorts = [ 80 ];

    environment.systemPackages = with pkgs; [
      iperf
      iperf2
      netperf
    ];

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
}
