# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {};

runCommand "dummy" { buildInputs = [ (python.withPackages(ps:[ps.mininet-python])) ]; } ""
