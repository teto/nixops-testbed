let
  libvirtd-base = {
      headless = true;

      baseImageSize = 4; # GB
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


# virsh pool-create-as default dir --target /var/lib/libvirt/images
# virsh pool-dumpxml default > pool.xml
# virsh pool-define pool.xml 
# virsh pool-autostart default

      # to see the botting message on the line
      # some of it could be passed as 
      # don't need the ip=dhcp anymore
      # boot.trace to look at startup commands
      # nokaslr needed for qemu debugging
      # cmdline=" earlycon=ttyS0 console=ttyS0 boot.debug=1";
      # cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 boot.consoleLogLevel=1 nokaslr";
      # # x86_64 is a symlink towards x86
      # kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";
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

  # TODO look at https://libvirt.org/formatdomain.html coredump-destroy
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
    <on_crash>coredump-destroy</on_crash>
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
  # client = { config, pkgs, lib, ...} @ args:
  # # lib.traceShowVal 
  # lib.recursiveUpdate (libvirtd-local args) { 
  #   deployment.libvirtd.template = debug_domain; 
  #   # create it with `virsh -c qemu:///system`
  #   # $ net-define --file /home/teto/testbed/templates/libvirtd-network.xml
  #   # net-start mptcpB
  #   # net-autostart mptcpB
  #   # this is the versions working with master 
  #   # deployment.libvirtd.networks = [ "default" "mptcpB" ]; 

  #   # this is the versions https://github.com/NixOS/nixops/pull/922
  #   deployment.libvirtd.networks = [ 
  #     # if any problem with default network, it can be recreated with
  #     # doc says virsh net-define /usr/share/libvirt/networks/default.xml
  #     # but on nixos it is 
  #     # net-define ${libvirt}var/lib/libvirt/qemu/networks/default.xml
  #     { source = "default"; type= "virtual"; }
  #     # { source="mptcpB"; type="bridge"; }
  #   ]; 
  # };

}
