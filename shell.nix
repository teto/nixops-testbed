{ pkgs ? import <nixpkgs> {} }:

# marche:
# nix-shell -p 'python3.withPackages(ps: with ps; [ pandas (matplotlib.override { enableGtk3=true;enableQt=true;}) pygobject3])' gobjectIntrospection gtk3

# let 
  # pycairo
  # pyEnv = pkgs.python3.withPackages(ps: with ps; [
  #   pandas
  #   # enableQt=true;
  #   (matplotlib.override { enableGtk3=true;enableQt=true;})
  #   pyqt5
  #   pygobject3
  # ] );
# in
#   pyEnv.env
  pkgs.python3Packages.callPackage ./default.nix {}
