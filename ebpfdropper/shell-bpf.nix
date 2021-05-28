# linux-headers  
# make $(linux-headers)/samples/bpf/ LLC=~/git/llvm/build/bin/llc CLANG=~/git/llvm/build/bin/clang
# clang -O2 -emit-llvm -c bpf.c -o - | llc -march=bpf -filetype=obj -o bpf.o

/* nix-shell -E 'with import <nixpkgs> {}; clangStdenv.mkDerivation { hardeningDisable=["all"]; name = "name"; buildInputs = [llvm_5];}' */
{ pkgs ? import <nixpkgs> {} }:

# pkgs.mkShell {
#   # this will make all the build inputs from hello and gnutar available to the shell environment
#   # inputsFrom = with pkgs; [ hello gnutar ];

# # TODO add shell hook to export LLC / CLANG
# # runCommand "dummy" { 
#   buildInputs = with pkgs; [ 
#   # iperf3 (python.withPackages(ps:[ps.mininet-python])) 
#   # ((linuxPackagesFor mptcp-local-stable).bcc)
#     # mptcp-local-stable.dev 

#     llvm_4 # for llc
#     clang # for clang
#   ]; 

#   # export LLC=${pkgs.llvm_4}
#   shellHook = ''
#     echo "hello world"
#   '';
# }

pkgs.ebpfdropper
