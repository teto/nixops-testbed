# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {};

let

  # mininet-python = pythonPackages.mininet-python.overrideAttrs(oa: {
  #   src = /home/teto/mininet;
  # });
  a= 2;
in
runCommand "dummy" { buildInputs = [ iperf3 (python.withPackages(ps:[ps.mininet-python])) ]; } ""
