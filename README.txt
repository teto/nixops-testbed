
1. Enable libvirtd on your system
2. Run `nix develop`
3. Create your VMs if they dont exist already:
`nixops create ./mptcp-local-logical.nix ./mptcp-local-physical.nix`
`nixops deploy --debug`



