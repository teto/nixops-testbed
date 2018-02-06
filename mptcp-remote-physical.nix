let
  secrets = import ./secrets.nix;
  nixos-remote = { config, pkgs, ... }:
  {
    deployment.targetHost = secrets.mptcp_server.ip4.address;
  };
in
{
  network.description = "MPTCP testing";
  server = nixos-remote;
}

