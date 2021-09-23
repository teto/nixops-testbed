{
  description = "A very basic flake";

  inputs = {
    nixops.url = "github:nixos/nixops";
    mptcp.url = "github:teto/mptcp-flake";
    # perso.url = "github:teto/home";
    utils.url = "github:numtide/flake-utils";
    # nixops-libvirtd.url = "github:teto/nixops-libvirtd/flake";

    # use as a backup solution until nixops gets its shit together
    # nixops-plugged.url = "github:lukebfox/nixops-plugged";
    iohk-nixops.url = "github:input-output-hk/nixops-flake";
  };

  outputs = inputs@{ self, mptcp, nixpkgs, nixops, utils, ... }: let
  in utils.lib.eachSystem ["x86_64-linux"] (system: let
      pkgs = import nixpkgs {
          inherit system;
          # overlays = pkgs.lib.attrValues (self.overlays);
          config = {
            # allowUnfree = true;
            # allowBroken = true;
          };
        };
  in {

    defaultPackage = nixops.defaultPackage."${system}".withPlugins(ps: [
      ps.nixops-libvirtd
    ]);
    # defaultPackage = pkgs.mkShell {
    #   name = "testbed";
    #   buildInputs = [
    #     inputs.nixops.defaultPackage."${system}"
    #   ];
    # };

    devShell = pkgs.mkShell {
      name = "devshell";
      buildInputs = [
        inputs.iohk-nixops.packages."${system}".nixops_2_0-latest-unstable
      ];
    };

  }) // {

    nixosConfigurations = {
      # mininet-server = nixpkgs.lib.nixosSystem {
      #   # ./.
      # };
    };
  };
}
