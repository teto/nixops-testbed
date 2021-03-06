# after deployement run
# nixops ssh-for-each "ln -s /dev/sda1 /dev/root"
{ multihomed ? false , ... }:
let
  tpl = { config, pkgs, lib,  ... }:
  let
    logger = "${pkgs.utillinux}/bin/logger";

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

  in
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        # /home/teto/dotfiles/nixpkgs/config-all.nix

        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];

  programs.wireshark.enable = true; # installs setuid
  programs.wireshark.package = pkgs.tshark; # which one

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
    # one of "OFF", "ERR", "WARN", "INFO", "DEBUG", "TRACE"
    logLevel="DEBUG";

    # TODO reestablish with the correct nixpkgs !
    dispatcherScripts = [
      # {
      #   source = mptcpUp;
      #   # type = "up";
      # }

      # netem-based hooks
      # {
      #   source = addDelay;
      # }
    ];
  };

    # TODO test with
    networking.mptcp.enable = true;
    # networking.iproute2.enable = true;

    # TODO run commands on boot

    # TODO use webfs instead ?
    # services.httpd.enable = true;
    # services.httpd.adminAddr = "alice@example.org";
    # services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    networking.firewall.enable = false;

    # just trying
    networking.resolvconf.dnsExtensionMechanism = false;
    networking.resolvconf.dnsSingleRequest = false;


    boot.postBootCommands = ''
      ln -s /dev/sda1 /dev/root
    '';

    environment.systemPackages = with pkgs; [
      at # to run in background
      ethtool # to check for segmentation offload
      tmux   # to have it survive ssh closing, nohup can help too
      iperf
      iperf2
      netperf
      ncdu
      tshark
      host.dnsutils
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
