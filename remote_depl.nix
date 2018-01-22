
+    deployment.libvirtd.URI = mkOption {
+      type = types.str;
+      default = "qemu:///system";
+      description = ''
+        Connection URI.
+      '';
+    };
