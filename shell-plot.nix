with import <nixpkgs> {};

# runCommand "dummy42" { buildInputs = [ (python3.withPackages(ps: with ps;[ pandas])) ]; } ""

runCommand "dummy2" {
  buildInputs = with python3Packages; [
    pandas 
    # we want gtk because qt is so annying on nixos
    (matplotlib.override { enableGtk3=true;})
    # pyqt5
]; 
} ""

  # pkgs.python3Packages.callPackage ./default.nix {}
# # marche:
# # nix-shell -p 'python3.withPackages(ps: with ps; [ pandas (matplotlib.override { enableGtk3=true;}) ])' 

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

# c le seul truc qui marche
# { pkgs ? import <nixpkgs> {} }:
# pkgs.python3Packages.callPackage ./random.nix {}
