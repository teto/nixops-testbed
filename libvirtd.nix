let
  libvirtd = { config, pkgs, ... }:
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
    # <interface type='network'>
    #   <source network='default'/>
    #   <model type='e1000'/>
    # </interface>
      # je laisse la mac a part <mac address='52:54:00:4b:38:3d'/>
      # potentially might set networks to 0
      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # to see the botting message on the line
      # this can be used for nix ${config.system.build.toplevel}/init
      cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 boot.consoleLogLevel=1 ip=dhcp";
      # initrd = ""
      # todo set it to my local vmimage
      kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";
      # kernel=/tmp/vmlinux;
      # initrd=/tmp/vmlinux;
    };

    # test improvements
    # deployment.libvirtd.kernel = "otot";
  };
in
{
  # example = libvirtd;
  server = libvirtd;
  # client = libvirtd;
}
