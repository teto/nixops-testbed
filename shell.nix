{ pkgs ? import <nixpkgs> {} }:

let 
  pyEnv = pkgs.python3.withPackages(ps: with ps; [ pandas matplotlib pycairo ] );

in
  pyEnv.env
