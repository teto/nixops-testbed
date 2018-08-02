
make samples/bpf/ LLC=~/git/llvm/build/bin/llc CLANG=~/git/llvm/build/bin/clang


# inspired by https://github.com/bjornfor/nixos-config


sudo mv /etc/nixos /etc/nixos.bak
sudo git clone https://github.com/bjornfor/nixos-config /etc/nixos
sudo cp /etc/nixos.bak/hardware-configuration.nix /etc/nixos/
sudo ln -sr /etc/nixos/machines/$MACHINE.nix /etc/nixos/configuration.nix

nixops create -d matt ~/testbed/libvirtd.nix ~/testbed/main.nix --debug
