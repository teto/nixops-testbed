# inspired by https://nixos.org/nix/manual/#sec-nix-shell
with import <nixpkgs> {};

let
  startPlugins = with pkgs.vimPlugins; [
            fugitive
            vimtex
            # replaced by ale ?
            LanguageClient-neovim
            vim-signify
            vim-startify
            vim-scriptease
            vim-grepper
            vim-nix
            vim-obsession
            # deoplete-khard
            # TODO this one will be ok once we patch it
            # vim-markdown-composer  # WIP
# vim-highlightedyank
        ];
  neovimDefaultConfig = {
        withPython3 = true;
        withPython = false;
        withRuby = true; # for vim-rfc/GhDashboard etc.
        customRC = ''
          " always see at least 10 lines
          set scrolloff=10
          set hidden

        " Failed to start language server: No such file or directory: 'pyls'
        " todo do the same for pyls/vimtex etc
        let g:vimtex_compiler_latexmk = {}
        " latexmk is not in combined.small/basic
        " vimtex won't let us setup paths to bibtex etc, we can do it in .latexmk ?

        let g:LanguageClient_serverCommands = {
             \ 'python': [ fnamemodify( g:python3_host_prog, ':p:h').'/pyls', '--log-file' , expand('~/lsp_python.log')]
             \ , 'haskell': ['hie', '--lsp', '-d', '--logfile', '/tmp/lsp_haskell.log' ]
             \ , 'cpp': ['${pkgs.cquery}/bin/cquery', '--log-file=/tmp/cq.log']
            \ , 'c': ['${pkgs.cquery}/bin/cquery', '--log-file=/tmp/cq.log']
             \ }

        ''
        ;

    configure = {
        packages.myVimPackage = {
          # see examples below how to use custom packages
          # loaded on launch
          start = startPlugins;
          # manually loadable by calling `:packadd $plugin-name`
          opt = [ ];
        };
      };

    extraPython3Packages = ps: with ps; [
      pandas
      jedi
      urllib3
      # pygments # for pygmentize and minted in latex
      mypy
      # pyls-mypy # on le desactive sinon il genere des
      # python-language-server
      pycodestyle
    ]
      # ++ lib.optionals ( pkgs ? pyls-mypy) [ pyls-mypy ]
    ;

  };

  # mininet-python = pythonPackages.mininet-python.overrideAttrs(oa: {
  #   src = /home/teto/mininet;
  # });
  # a= 2;
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

  nvimConfig = neovimConfig (lib.mkMerge [
    neovimDefaultConfig
    {
      extraPython3Packages = python3PackagesFun;
    }
  ]);

  # wrapNeovim neovim-unwrapped
  my_nvim = wrapNeovim neovim-unwrapped (
    lib.mkMerge [
    neovimDefaultConfig
    {
      extraPython3Packages = python3PackagesFun;
    }
    ]
  );

  # TODO wrap neovim in fact
  # pythonEnv = python3.withPackages();
in
  mkShell {
    propagatedBuildInputs = [
      iperf3 my_nvim
      nvimConfig.python3Env
    ];

    # $(which python3)
    # my_
    # echo "${builtins.toString nvimConfig.python3Env}"
      # echo "let g:python3_host_prog='${pythonEnv.interpreter}'" > .nvimrc
    shellHook = ''
      echo "toto"
      echo "${builtins.toString nvimConfig.python3Env}"
    '';
  }
