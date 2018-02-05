rec {
  # network seems like a special attribute
  # the others are logical machines
  network = {
    description = "MPTCP testing";
    enableRollback = true;
  };
  server = import /home/teto/dotfiles/nixpkgs/config-iij-mptcp.nix;
}
