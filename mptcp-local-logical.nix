# after deployement run
# nixops ssh-for-each "ln -s /dev/sda1 /dev/root"
{ multihomed ? false , ... }:
let
  tpl = { config, pkgs, lib,  ... }:
  let
    ip = "${pkgs.iproute}/bin/ip";
    logger = "${pkgs.utillinux}/bin/logger";
    
    # networkmanager hooks
    mptcpUp =   /home/teto/dotfiles/nixpkgs/hooks/mptcp_up_raw;
    mptcpDown =  /home/teto/dotfiles/nixpkgs/hooks/mptcp_down_raw;

    ifCheck= ''
      if [ "$DEVICE_IFACE" = lo ]; then
          logger -t mptcp_up "if localhost or $MODE then abort "
          exit 0
      fi

      if [ -z "$DEVICE_IFACE" ]; then
          logger "invalid \$DEVICE_IFACE"
          exit 0
      fi
      '';

    addDelay = pkgs.writeText "add_delay" ''
      ${ifCheck}

      if [ "$EVENT" != "up" ]; then
          logger "exit $EVENT != down"
      fi

      logger "adding delay"
      set -x


      # remove it just in case it already exists
      tc qdisc del dev "$DEVICE_IFACE" root netem
      # here we can add some variance https://netbeez.net/blog/how-to-use-the-linux-traffic-control/
      # via appending a 10ms
      tc qdisc add dev "$DEVICE_IFACE" root netem delay 100ms
    '';

    removeDelay = pkgs.writeText "remove_delay" ''

      ${ifCheck}

      if [ "$EVENT" != "up" ]; then
          logger "exit $EVENT != down"
      fi

      logger "removing delay"

      set -x
      tc qdisc del dev "$DEVICE_IFACE" root netem
    '';

    myOverlay = /home/teto/dotfiles/nixpkgs/overlays/kernels.nix;
  in
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        # /home/teto/dotfiles/config/nixpkgs/overlays/kernels.nix
        /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix
        /home/teto/dotfiles/nixpkgs/common-all.nix
        /home/teto/dotfiles/nixpkgs/common-server.nix
        /home/teto/dotfiles/nixpkgs/modules/wireshark.nix
        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];

      # moved it
  # system.activationScripts.createDevRoot = ''
  #   # if does not exist ?!
  #   ln -s /dev/sda1 /dev/root
  # '';

  # mptcp-manual
  # boot.kernelPackages = pkgs.linuxPackages_mptcp-local;
  # boot.kernelPackages = pkgs.linuxPackagesFor pkgs.mptcp-manual;

  # WARNING: pick a kernel along the same version as tc ?
  # boot.kernelPackages = pkgs.linuxPackages_mptcp;
  boot.blacklistedKernelModules = ["nouveau"];

  boot.kernelParams = [ "earlycon=ttyS0" "console=ttyS0" "boot.debug=1" "boot.consoleLogLevel=1" ];

  networking.networkmanager = {
    enable=true;
    # enableStrongSwan = true;
    # one of "OFF", "ERR", "WARN", "INFO", "DEBUG", "TRACE"
    logLevel="DEBUG";
    # wifi.scanRandMacAddress = true;

    # TODO reestablish with the correct nixpkgs !
    dispatcherScripts = [
      {
        source = mptcpUp;
        # type = "up";
      }
      # {
      #   source = mptcpDown;
      #   # type = "down";
      # }
      # netem-based hooks
      {
        source = addDelay;
        # type = "up";
      }
      # {
      #   source = removeDelay;
      #   # type = "down";
      # }
    ];

    # networking.resolvconfOptions
    # wifi.powersave=false;
    # TODO configure dispatcherScripts  for mptcp
  };


    nixpkgs.overlays = lib.optionals (builtins.pathExists myOverlay)  [ (import myOverlay) ]
    ;

    # TODO run commands on boot

    # TODO use webfs instead ?
    # services.httpd.enable = true;
    # services.httpd.adminAddr = "alice@example.org";
    # services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    networking.firewall.enable = false;

    # just trying
    networking.dnsExtensionMechanism = false;
    networking.dnsSingleRequest = false;

    networking.iproute2.enable = true;
    # boot.postBootCommands = ''
    #   ln -s /dev/sda1 /dev/root
    # '';

    environment.systemPackages = with pkgs; [
      at # to run in background
      ethtool # to check for segmentation offload
      tmux   # to have it survive ssh closing, nohup can help too
      iperf
      iperf2
      netperf
      tshark
    ];

    # TODO here we can set a custom initramfs/kernel
    # see my work on vagrant libvirt
    # <log file="/var/log/libvirt/qemu/guestname-serial0.log" append="off"/>
    # virsh + ttyconsole pour voir le numero
    # TODO maybe add users

  } 
  );


  # client_tpl = {config, pkgs, ... } @ args:
  # (tpl args);
  # // {
    # need to be multihomed
    # networking.interfaces = {
    #   eth0 = { name = "eth0"; useDHCP=true; };
    #   # eth1 = { name = "eth1"; useDHCP=true; };
    # };

    # networking.firewall.enable = false;
    # # to execute at the end of a setupped network
    # # networking.localCommands=
  # };
in
rec {
  # network seems like a special attribute
  # the others are logical machines
  network = {
    description = "local MPTCP";
    enableRollback = false;
  };

  # server = tpl ;
  # <custom/>
  # server = import /home/teto/dotfiles/nixpkgs/config-iij-mptcp.nix;
  # 
  server = {  config, pkgs, lib,  ... } @ args: 
    tpl args // {
      # TODO configure for 
      # now that we have qemu-agent it should be possible to use static ip addresses too
      # networking.interfaces = {
      #   ipv4.addresses = [ { address = "10.0.0.1"; prefixLength = 16; } { address = "192.168.1.1"; prefixLength = 24; } ]
      # ipv4.routes = [ { address = "10.0.0.0"; prefixLength = 16; } { address = "192.168.2.0"; prefixLength = 24; via = "192.168.1.1"; } ]
      # };
    };
  client = tpl;
}
