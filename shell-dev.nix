  # pyEnv = my_nvim.config.python3Env;

  import ./shell-mininet.nix { host = true; }
  # pyEnv = python3Packages.withPackages(python3PackagesFun);

  # # wrapNeovim neovim-unwrapped
  # # my_nvim = wrapNeovim neovim-unwrapped (
  # #   lib.mkMerge [
  # #   neovimDefaultConfig
  # #   {
  # #     extraPython3Packages = python3PackagesFun;
  # #   }
  # #   ]
  # # );

# in
  # mkShell {
  #   propagatedBuildInputs = [
  #     iperf3
  #   ];

  #   # echo "${builtins.toString nvimConfig.python3Env}"
  #   shellHook = ''
  #    export PATH="${my_nvim}/bin:$PATH"
  #    echo "toto"
  #     echo "${my_nvim}"
  #   '';
  # }

