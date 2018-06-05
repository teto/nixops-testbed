{ pkgs ? import <nixpkgs> {} }:

# # marche:
# # nix-shell -p 'python3.withPackages(ps: with ps; [ pandas (matplotlib.override { enableGtk3=true;enableQt=true;}) pygobject3])' gobjectIntrospection gtk3

# let 
#   pyEnv = pkgs.python3.withPackages(ps: with ps; [
#     pandas
#     # enableQt=true;
#     # enableGtk3 adds stdenv.lib.optionals enableGtk3 [ cairo pycairo gtk3 gobjectIntrospection pygobject3 ]
#     (matplotlib.override { enableGtk3=true;})
#     # (matplotlib.override { enableQt=true;})
#     # pyqt5
#     # tshark
#     # pygobject3
#   ] );
# in
#   pyEnv.env
  pkgs.python3Packages.callPackage ./default.nix {}
