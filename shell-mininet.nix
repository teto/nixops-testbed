# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {};

let

  # mininet-python = pythonPackages.mininet-python.overrideAttrs(oa: {
  #   src = /home/teto/mininet;
  # });
  a= 2;
  pythonEnv = python3.withPackages(ps: with ps; [
      jedi
      urllib3 
      mypy
      pyls-mypy # on le desactive sinon il genere des
      python-language-server
      pycodestyle
      mininet-python
      # future
  ]);
in
  mkShell {
    buildInputs = [ iperf3 pythonEnv ]; 

    # $(which python3)
    shellHook = ''
      echo "let g:python3_host_prog='${pythonEnv.interpreter}'" > .nvimrc
    '';
  }
