let
  secrets = import <custom/secrets.nix>;
  nixos-remote = { config, pkgs, ... }:
  {
    deployment.targetHost = secrets.gitolite_server.ip4.address;
  };
in
{
  network.description = "Generate MPTCP pcap";
  gitolite-server = nixos-remote;
}
