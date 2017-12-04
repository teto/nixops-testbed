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
      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # to see the botting message on the line
      # this can be used for nix ${config.system.build.toplevel}/init
      cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init";
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
  client = libvirtd;
  server = libvirtd;
}
