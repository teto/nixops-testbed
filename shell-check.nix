# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {};

runCommand "dummy" { buildInputs = [ python ((linuxPackagesFor mptcp-local-stable).bcc) mptcp-local-stable.dev ]; } ""