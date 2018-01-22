let
  libvirtd-local = { config, pkgs, ... }:
  {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd = {
      headless = true;
      extraDevicesXML = ''
        <serial type='pty'>
        <target port='0'/>
        </serial>
        <console type='pty'>
        <target type='serial' port='0'/>
        </console>
      '';
      # potentially might set networks to 0
      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # to see the botting message on the line
      # some of it could be passed as boot.kernelParams = [ "console=ttyS0,115200" ];
      # don't need the ip=dhcp anymore
      # boot.trace to look at startup commands
      # cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 boot.consoleLogLevel=1 ";
      # kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";
    };

    # test improvements
    # deployment.libvirtd.kernel = "otot";
  };
  libvirtd-remote = { config, pkgs, ... }:
  {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd = {
      headless = true;
      extraDevicesXML = ''
        <serial type='pty'>
        <target port='0'/>
        </serial>
        <console type='pty'>
        <target type='serial' port='0'/>
        </console>
      '';
      # potentially might set networks to 0
      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # to see the botting message on the line
      # some of it could be passed as boot.kernelParams = [ "console=ttyS0,115200" ];
      # don't need the ip=dhcp anymore
      # boot.trace to look at startup commands
      # cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 boot.consoleLogLevel=1 ";
      # kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";
      # see for more details https://libvirt.org/remote.html
      # 202.214.86.51
      URI="qemu+ssh://iij_vm/system";
    };

    # test improvements
    # deployment.libvirtd.kernel = "otot";
  };
in
{
  # example = libvirtd;
  server = libvirtd-remote;
  client = libvirtd-local;
}
