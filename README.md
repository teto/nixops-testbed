# README

This repository aims at providing ways to generate MPTCP traffic in a local
controlled environnement: 
- virtual machines configurations that can be installed via [nixops].
- or via [mininet] containers.

creates virtual machines/containers to reproduce locally some 

1. Enable libvirtd on your system
2. Run `nix develop`
3. Create your VMs if they dont exist already:
`nixops create ./mptcp-local-logical.nix ./mptcp-local-physical.nix`
`nixops deploy --debug`


nixops: https://github.com/NixOS/nixops
mininet:
