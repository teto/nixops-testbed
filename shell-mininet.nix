# inspired by https://nixos.org/nix/manual/#sec-nix-shell
{
  host ? false
}:
with import <nixpkgs> {
  # overlays = [ (import ./neovim.nix) ];
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


  haskellDaemon = import ../mptcp-pm;

  my_nvim = genNeovim  [ ] {
    withHaskell = false;
    extraPython3Packages = python3PackagesFun;
  };

  nvimPyEnv = my_nvim.config.python3Env;

  standalonePyEnv = python3.withPackages(python3PackagesFun);

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
    name = "shell-for-mntest.py";
    propagatedBuildInputs = let
        pyEnv = (if host == true then nvimPyEnv else standalonePyEnv);
      in [
      iperf3
      pyEnv
      haskellDaemon
    ];

    # echo "${builtins.toString nvimConfig.python3Env}"
    # echo "${my_nvim}"
    # export PATH="${my_nvim}/bin:$PATH"
    shellHook = ''
      export SCRIPT="$(dirname ${./mn_test.py})"
     echo "Run as `nix-shell --arg host true shell-mininet.nix` if on the host"
     echo "toto"
    '';
  }
