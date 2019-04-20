# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {
  overlays = [ (import ./neovim.nix) ];
};


let

  python3PackagesFun = ps: with ps; [
      jedi
      urllib3
      mypy
      # pyls-mypy # on le desactive sinon il genere des
      # python-language-server
      # pycodestyle
      mininet-python
      # future
  ];

  my_nvim = genNeovim  [ ] {
    withHaskell = false;
    extraPython3Packages = python3PackagesFun;
  };

  # wrapNeovim neovim-unwrapped
  # my_nvim = wrapNeovim neovim-unwrapped (
  #   lib.mkMerge [
  #   neovimDefaultConfig
  #   {
  #     extraPython3Packages = python3PackagesFun;
  #   }
  #   ]
  # );

in
  mkShell {
    propagatedBuildInputs = [
      iperf3
      my_nvim.config.python3Env
    ];

    # echo "${builtins.toString nvimConfig.python3Env}"
    shellHook = ''
      echo "toto"
      echo "${my_nvim}"
    '';
  }
