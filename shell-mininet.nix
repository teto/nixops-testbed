# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {};

runCommand "dummy" { buildInputs = [ iperf3 (python.withPackages(ps:[ps.mininet-python])) ]; } ""
