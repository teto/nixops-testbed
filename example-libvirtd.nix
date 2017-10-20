let
  libvirtd = {
    deployment.targetEnv = "libvirtd";
    deployment.libvirtd.headless = true;

    # test improvements
    # deployment.libvirtd.kernel = "otot";
  };
in
{
  # example = libvirtd;
  client = libvirtd;
  server = libvirtd;
}
