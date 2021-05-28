{
  description = "A very basic flake";

  inputs = {
    nixops.url = "github:nixos/nixops";
    mptcp.url = "github:teto/mptcp-flake";
    # perso.url = "github:teto/home";
    utils.url = "github:numtide/flake-utils";
    nixops-libvirtd.url = "github:teto/nixops-libvirtd/flake";
  };

  outputs = inputs@{ self, mptcp, nixpkgs, nixops, utils, ... }: let
  in utils.lib.eachSystem ["x86_64-linux"] (system: let
      # pkgs = nixpkgs.legacyPackages."${system}";
      pkgs = import nixpkgs {
          inherit system;
          # overlays = pkgs.lib.attrValues (self.overlays);
          config = { allowUnfree = true; allowBroken = true; };
        };
  in {

    # packages."${system}".hello = nixpkgs.legacyPackages.x86_64-linux.hello;

    defaultPackage = inputs.nixops-libvirtd.defaultPackage."${system}";
    # defaultPackage = pkgs.mkShell {
    #   name = "testbed";
    #   buildInputs = [
    #     inputs.nixops.defaultPackage."${system}"
    #   ];
    # };
  }) // {

    nixosConfigurations = {
      # mininet-server = nixpkgs.lib.nixosSystem {
      #   # ./.
      # };
    };
  };
}
