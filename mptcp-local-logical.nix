# after deployement run
# nixops ssh-for-each "ln -s /dev/sda1 /dev/root"
{ multihomed ? false , ... }:
let
  tpl = { config, pkgs, lib,  ... }:
  let
    ip = "${pkgs.iproute}/bin/ip";
    logger = "${pkgs.utillinux}/bin/logger";
    
    # mptcpUp =   /home/teto/dotfiles/nixpkgs/hooks/mptcp_up_raw;
# builtins.readFile
    mptcpUp = writeScript ''
#!/bin/sh
set -ex

${pkgs.coreutils}/bin/env 
# > /tmp/if_up_env

if [ "$IFACE" = lo ] || [ "$MODE" != start ]; then

	${logger} "if localhost or $MODE then abort "
	exit 0
fi

if [ -z "$DEVICE_IFACE" ]; then

	${logger} "invalid \$DEVICE_IFACE"
	exit 0
fi

# mkdir -p /etc/iproute2
# FIRST, make a table-alias
if [ `grep "$DEVICE_IFACE" /etc/iproute2/rt_tables | wc -l` -eq 0 ]; then
	${logger} "Adding to iproute2/rt_tables \$DEVICE_IFACE"
	NUM=$(wc -l < /etc/iproute2/rt_tables)
	echo "$NUM  $DEVICE_IFACE" >> /etc/iproute2/rt_tables

fi

if [ "$DHCP4_IP_ADDRESS" ]; then
	SUBNET=`echo $IP4_ADDRESS_0 | cut -d \   -f 1 | cut -d / -f 2`
	${ip} route add table "$DEVICE_IFACE" to "$DHCP4_NETWORK_NUMBER/$SUBNET" dev "$DEVICE_IFACE" scope link
	${ip} route add table "$DEVICE_IFACE" default via $DHCP4_ROUTERS dev "$DEVICE_IFACE"
	${ip} rule add from $DHCP4_IP_ADDRESS table "$DEVICE_IFACE"
else
	# PPP-interface
	IPADDR=`echo $IP4_ADDRESS_0 | cut -d \   -f 1 | cut -d / -f 1`
	${ip} route add table $DEVICE_IFACE default dev $DEVICE_IP_IFACE scope link
	${ip} rule add from $IPADDR table $DEVICE_IFACE
fi
'';

mptcpDown =  /home/teto/dotfiles/nixpkgs/hooks/mptcp_down_raw;
    # mptcpDown = pkgs.writeScript "mptcp_down" ''
##!/bin/sh
#set -ex

## env > /tmp/if_down_env

#if [ "$IFACE" = lo -o "$MODE" != stop ]; then
#        exit 0
#fi

#${ip} rule del table $DEVICE_IFACE
#${ip} route flush table $DEVICE_IFACE 
#''

    in
  ({
    # prints everything superior to this number

    imports = [
      #  Not needed if we use the libvirt kernel interface
        /home/teto/dotfiles/nixpkgs/mptcp-unstable.nix
        /home/teto/dotfiles/nixpkgs/common-all.nix
        /home/teto/dotfiles/nixpkgs/common-server.nix
        /home/teto/dotfiles/nixpkgs/modules/wireshark.nix
        # for now don't use it
        # /home/teto/dotfiles/nixpkgs/modules/network-manager.nix
      ];

    boot.kernelParams = [ "earlycon=ttyS0" "console=ttyS0" "boot.debug=1" "boot.consoleLogLevel=1" ];

    # dispatcherScripts = [
    #   {
    #     source = ./mptcp_up ;
    #     type = "up";
    #   }
    #   {
    #     source = ./mptcp_down ;
    #     type = "down";
    #   }
    #   ];


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
        type = "up";
      }
      {
        source = mptcpDown;
        type = "down";
      }
    ];

    # networking.resolvconfOptions
    # wifi.powersave=false;
    # TODO configure dispatcherScripts  for mptcp
  };

    # nixpkgs.overlays = [ (import ./overlays/this.nix) (import ./overlays/that.nix) ]
    # nixpkgs.overlays = [
    #   (import /home/teto/dotfiles/config/nixpkgs/overlays/i3.nix)
    # ];

    # TODO run commands on boot

    # TODO use webfs instead ?
    # services.httpd.enable = true;
    # services.httpd.adminAddr = "alice@example.org";
    # services.httpd.documentRoot = "${pkgs.valgrind.doc}/share/doc/valgrind/html";
    networking.firewall.enable = false;

    # just trying
    networking.dnsExtensionMechanism = false;
    networking.dnsSingleRequest = false;

    # allowedTCPPorts = [ 80 ];
    # networking.networkmanager = {
    #   enable=true;
    # #   # one of "dhclient", "dhcpcd", "internal"
    # #   dhcp="dhcpcd";
    # #   # networking.networkmanager.useDnsmasq
    # # #   enableStrongSwan = true;
    # # #   # one of "OFF", "ERR", "WARN", "INFO", "DEBUG", "TRACE"
    # # #   logLevel="DEBUG";
    # # #   wifi.scanRandMacAddress = true;
    # };

    # contradicts networkmanager
    # networking.useDHCP = true;

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
  server = tpl;
  client = tpl;
}
