let
  libvirtd-base = {
      headless = true;
      # <domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
      # domainType = "kvm\" xmlns:qemu=\"http://libvirt.org/schemas/domain/qemu/1.0";
      domainType = "kvm";
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
      # nokaslr needed for qemu debugging
      cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 boot.consoleLogLevel=1 nokaslr";
      # x86_64 is a symlink towards x86
      kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";
  };

  # lib.recursiveUpdate { } {deployment.libvirtd}
  libvirtd-local = { config, pkgs, ... }: {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd = libvirtd-base;
  };

  libvirtd-remote = { config, pkgs, ... }:
  {
    deployment.targetEnv = "libvirtd";

    deployment.libvirtd = libvirtd-base // {
      # see for more details https://libvirt.org/remote.html
      # 202.214.86.51
      URI="qemu+ssh://iij_vm/system";
    };

    # test improvements
    # deployment.libvirtd.kernel = "otot";
  };
  debug_domain = ''<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
	<qemu:commandline>
		<qemu:arg value='-s'/>
	</qemu:commandline>
  <name>{name}</name>
  <memory unit="MiB">{memory_size}</memory>
  <vcpu>{vcpu}</vcpu>
  {os}
  <devices>
	  <emulator>{emulator}</emulator>
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2"/>
      <source file="{diskPath}"/>
      <target dev="hda"/>
    </disk>
	{interfaces}
    <input type="keyboard" bus="usb"/>
    <input type="mouse" bus="usb"/>
	{extra_devices}
  </devices>
  {extra_domain}
</domain>'';
in
{
  # example = libvirtd;
  # server = libvirtd-remote;
  server = libvirtd-local;

  # we configure the debug domain just for one VM since -s for the 2 generates an error
  # in the port
  # client = libvirtd-local;
  client = { config, pkgs, lib, ...} @ args:
  # lib.traceShowVal 
  lib.recursiveUpdate (libvirtd-local args) { deployment.libvirtd.template = debug_domain; };

}
