# deployment.virtualbox.sharedFolders.home
{

  main = { config, pkgs, ... }:  {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd.networks = [
      { source = "default"; type= "virtual"; }
    ];
  };
}
