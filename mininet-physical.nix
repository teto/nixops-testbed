# deployment.virtualbox.sharedFolders.home
# see https://blog.mayflower.de/5976-From-Vagrant-to-Nixops.html
# for the virtualbox inspiration
{

  # look at http://rabexc.org/posts/p9-setup-in-libvirt
  # for how to setup shared folders
  main = { config, pkgs, ... }:  {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd = {
      baseImageSize = 8; # GB
      memorySize = 1024; # MB

      # TODO keep for later
      #  boot.consoleLogLevel=1
      cmdline="root=/dev/sda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 nokaslr tcp_probe.port=5201 tcp_probe.full=1";
      # # # x86_64 is a symlink towards x86
      kernel="/home/teto/mptcp/build/arch/x86_64/boot/bzImage";

      # this is the default
      # networks = [ { source = "default"; type= "virtual"; } ];
      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # To mount the folder
      # mount testbed ./testbed -t 9p -o trans=virtio
      # maybe I need to add a fileSystem ?
      extraDevicesXML = ''
        <serial type='pty'>
        <target port='0'/>
        </serial>
        <console type='pty'>
        <target type='serial' port='0'/>
        </console>
        <filesystem type='mount' accessmode='passthrough'>
            <source dir='/home/teto/testbed'/>
            <target dir='testlabel'/>
        </filesystem>
        <filesystem type='mount' accessmode='passthrough'>
            <source dir='/home/teto/mininet'/>
            <target dir='mnlabel'/>
        </filesystem>
      '';
    };

    # might trump boot
    #fileSystems."/mininet" = {
    #  device = "mnlabel";
    #  fsType = "9p";
    #  options = [ "uid=1000" 
    #    # "trans=virtio"
    #      # allow for it to be written
    #      # TODO use users gid ? or create a teto one ?
    #      #"gid=33" 
    #    ];
    #};
    #fileSystems."/testbed" = {
    #  device = "testlabel";
    #  fsType = "9p";
    #  options = [ "uid=1000" 
    #    # "trans=virtio"
    #      # allow for it to be written
    #      # TODO use users gid ? or create a teto one ?
    #      #"gid=33" 
    #    ];
    #};

    # VIRTUALBOX config 
    #deployment.targetEnv = "virtualbox"; # section 2
    #deployment.virtualbox = {
    #  memorySize = 1024;
    #  headless = true;
    #};

    #virtualisation.virtualbox.guest.enable = true;

    #deployment.virtualbox.sharedFolders = {
    #  # eventually mount mininet ?
    #  main = {
    #    # where we have the mininet scripts
    #    hostPath = "/home/teto/testbed";
    #    readOnly = false;
    #  };
    #};


    ## to mount
    #fileSystems."/testbed" = { # section 5
    #  device = "main";
    #  fsType = "vboxsf";
    #  options = [ "uid=1000" 
    #      # allow for it to be written
    #      # TODO use users gid ? or create a teto one ?
    #      #"gid=33" 
    #    ];
    #};
  };
}
