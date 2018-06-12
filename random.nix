{
stdenv
, fetchFromGitHub
, buildPythonApplication
, stevedore, cmd2
# might be useless ? depends on cmd2
, pyperclip
, pandas, matplotlib, pyqt5

# can be overriden with the one of your choice
, tshark
}:

buildPythonApplication rec {
	pname = "test";
	version = "0.1";

    # src = ./.;

    doCheck = false;

    # to build the doc sphinx
    propagatedBuildInputs = [ 
      pandas 
      # we want gtk because qt is so annying on nixos
      # matplotlib
      (matplotlib.override { enableGtk3=true;})
      pyqt5
      tshark 
    ];

    meta = with stdenv.lib; {
      description = "pcap analysis tool specialized for multipath TCP";
      maintainers = [ maintainers.teto ];
      license = licenses.gpl3;
    };
}

