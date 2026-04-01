{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libffi
    ];
    PYTHONBIN = "${pkgs.python312}/bin/python3.12";
    LANG = "en_US.UTF-8";
  };
}
