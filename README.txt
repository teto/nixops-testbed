
By default, the hosts are put in their own namespace, while switches and the controller are in the root namespace. To put switches in their own namespace, pass the --innamespace option:

# deploy with 
> nixops deploy -I nixos-config=/home/teto/dotfiles/nixpkgs/configuration-lenovo.nix  -dmn5

# generate ebpf bytecode

$ nix-shell -A ebpfdropper ~/nixpkgs
$ clang -O2 -emit-llvm -c ebpf_dropper.c -o - | llc -march=bpf -filetype=obj -o ebpf_dropper.o && ./attach_tc.sh eth0

# generate the file to be dropped

$ ./gen-file

will create a file that appends DROPME at its end


ebpf_dropper seen at:
https://github.com/francoismichel/ebpf_dropper/tree/networking_2019



https://multipath-tcp.org/pmwiki.php/Users/Tools
  ip link set dev eth0 multipath off
  ip link set dev eth0 multipath backup
