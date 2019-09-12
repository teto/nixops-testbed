# deployment.virtualbox.sharedFolders.home
# see https://blog.mayflower.de/5976-From-Vagrant-to-Nixops.html
# for the virtualbox inspiration
{

  # look at http://rabexc.org/posts/p9-setup-in-libvirt
  # for how to setup shared folders
  main = { config, pkgs, ... }:
    let
      # "posixacl"
      # version=9p2000.L must be one of the recent versions
      # how to access logs of "debug=0x04"
      # https://www.kernel.org/doc/Documentation/filesystems/9p.txt
      options9p = [ "defaults" "nofail" "access=any" "trans=virtio" "version=9p2000.L" ];
      # make it very slow : ++ [ "debug=0x05" ]
    in
    {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd = {
      baseImageSize = 14; # GB
      memorySize = 2048; # MB

      # TODO keep for later
      #  boot.consoleLogLevel=1

      # https://serverfault.com/questions/803388/what-is-the-difference-between-dev-vda-and-dev-sda
      # vda => paravirtualized, should be faster
      # sda => fullyvirtualized, should be slower ?


      # for now it looks too dangerous aka it doesn't seem to work
      # cmdline="root=/dev/vda1 earlycon=ttyS0 console=ttyS0 init=/nix/var/nix/profiles/system/init boot.debug=1 raid=noautodetect nokaslr";
      # kernel="/home/teto/bzImage";

      # added in https://github.com/NixOS/nixops/pull/922
      storagePool = "ext";

      # this is the default
      # networks = [ { source = "default"; type= "network"; } ];

      extraDomainXML = ''
        <on_crash>preserve</on_crash>
      '';

      # To mount the folder
      # maybe I need to add a fileSystem ?
      # mount testlabel /testbed -t 9p -o trans=virtio
      # mount mnlabel /mininet -t 9p -o trans=virtio

      # on passthrough modes http://rabexc.org/posts/p9-setup-in-libvirt
      # mapped/passthrough/none
      # mapped
      # To have files created and accessed as the user running kvm/qemu. Uses extended attributes to store the original user credentials.
      # passthrough
      # To have files created and accessed as the user within kvm/qemu.
      # none
      # Like passthrough, except failures in privileged operations are ignored.

      # <filesystem type='mount' accessmode='passthrough'>
      #     <source dir='/home/teto'/>
      #     <target dir='xp'/>
      # </filesystem>

      extraDevicesXML = ''
        <serial type='pty'>
        <target port='0'/>
        </serial>
        <console type='pty'>
        <target type='serial' port='0'/>
        </console>
        <filesystem type='mount' accessmode='mapped'>
            <source dir='/home/teto/mptcp'/>
            <target dir='mptcp'/>
        </filesystem>
        <filesystem type='mount' accessmode='mapped'>
            <source dir='/home/teto/testbed'/>
            <target dir='mn'/>
        </filesystem>
        <filesystem type='mount' accessmode='passthrough'>
            <source dir='/home/teto/mptcp-pm'/>
            <target dir='netlink'/>
        </filesystem>
        <filesystem type='mount' accessmode='passthrough'>
            <source dir='/home/teto/mininet'/>
            <target dir='mininet'/>
        </filesystem>
        <filesystem type='mount' accessmode='passthrough'>
            <source dir='/home/teto/nixpkgs'/>
            <target dir='nixpkgs'/>
        </filesystem>
      '';
    };

    # add entry for fs ?
        # <filesystem type='mount' accessmode='passthrough'>
        #     <source dir='/home/teto/out'/>
        #     <target dir='xp'/>
        # </filesystem>


    networking.firewall.enable = false;

     # might trump boot
     # nofail Do not report errors for this device if it does not exist
     # Mount points are created automatically if they don’t already exist.
    #fileSystems."/root/mininet" = {
    #  device = "mn";
    #  fsType = "9p";
    #  options = [
    #    # "uid=1000" 
    #    # "trans=virtio"
    #      # allow for it to be written
    #      # TODO use users gid ? or create a teto one ?
    #      #"gid=33" 
    #      "nofail"
    #    ];
    #};

    # We don't want to mount our home since it will break tons of symlink => bash
    # fileSystems."/home/teto" = {
    #   device = "xp";
    #   fsType = "9p";
    #   options = [
    #     "nofail" 
    #     # "ro" might generate errors
    #     # "ro"
    #   ];
    # };
    fileSystems."/home/teto/testbed" = {
      device = "mn";
      fsType = "9p";
      options = options9p ;
    };
    fileSystems."/home/teto/mptcp" = {
      device = "mptcp";
      fsType = "9p";
      options = options9p ;
    };
    # fileSystems."/home/teto/frite" = {
    #   device = "frite";
    #   fsType = "9p";
    #   options = options9p;
    # };

    fileSystems."/home/teto/mptcp-pm" = {
      device = "netlink";
      fsType = "9p";
      options = options9p;
    };

    fileSystems."/home/teto/mininet" = {
      device = "mininet";
      fsType = "9p";
      # make it readonly
      options = options9p ++ [ "ro"];
    };
    fileSystems."/home/teto/nixpkgs" = {
      device = "nixpkgs";
      fsType = "9p";
      # make it readonly
      options = options9p ++ [ "ro"];
    };

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


    };
}
