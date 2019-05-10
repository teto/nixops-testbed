#!/bin/sh
# A script for setting up routing tables for MPTCP

# can check with (ins)[root@client:~]# journalctl -b -u NetworkManager-dispatcher.service
# Copy this script into /etc/network/if-up.d/
TAG1
7.7.7.1
# https://developer.gnome.org/NetworkManager/unstable/NetworkManager.html
set -ex

STATUS=$2
PREFIX="mptcp"
RT_TABLE=/etc/iproute2/rt_tables

env > /tmp/if_up_env

if [ "$DEVICE_IFACE" = "lo" ]; then

	echo "$PREFIX: if localhost or $MODE then abort "
	exit 0
fi

if [ -z "$DEVICE_IFACE" ]; then
	# logger -p user.warn -t mptcp
	echo "invalid interface [$DEVICE_IFACE]"
	exit 0
fi

if [ $(grep -c "$DEVICE_IFACE" "$RT_TABLE") -eq 0 ]; then
	echo "$PREFIX: Adding new routing table $DEVICE_IFACE"
	NUM=$(wc -l < "$RT_TABLE")
	echo "$NUM  $DEVICE_IFACE" >> "$RT_TABLE"
fi

# TODO do it for ipv6 too
# GATEWAY=
if [ -n "$DHCP4_IP_ADDRESS" ]; then
	SUBNET=`echo $IP4_ADDRESS_0 | cut -d \   -f 1 | cut -d / -f 2`
	ip route add table "$DEVICE_IFACE" to "$DHCP4_NETWORK_NUMBER/$SUBNET" dev "$DEVICE_IFACE" scope link
	ip route add table "$DEVICE_IFACE" default via $DHCP4_ROUTERS dev "$DEVICE_IFACE"
	ip rule add from "$DHCP4_IP_ADDRESS" table "$DEVICE_IFACE"
else
	# PPP or static interface 
	IPADDR=`echo $IP4_ADDRESS_0 | cut -d \   -f 1 | cut -d / -f 1`

	set +e
	# HAS_DEFAULT_ROUTE=$(ip route get default)
	# ip route get default

	# if [ $? -ne 0 ]; then
	# 	set -e
	# 	echo "Adding default route"
	# 	ip route add default via "$GATEWAY"
	# 	# dev "$DEVICE_IFACE"
	# 	# via "$DEVICE_IFACE"
	# fi

	# via "$GATEWAY"
	# la il nous manque des GW pour la configuration statique :/
	# set -e
	if [ -z "$IP4_GATEWAY" ]; then
		ip route add table "$DEVICE_IFACE" default via "$IP4_GATEWAY" dev "$DEVICE_IFACE"
	fi
	ip route add table "$DEVICE_IFACE" default  dev "$DEVICE_IP_IFACE" scope link
	ip rule add from "$IPADDR" table "$DEVICE_IFACE"
fi


