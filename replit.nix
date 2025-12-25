{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    
    # For transformers/torch
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.glibc
    
    # For audio/voice features (future)
    pkgs.ffmpeg
    pkgs.libopus
    pkgs.openssl
  ];
  
  env = {
    # Python path configuration
    PYTHONPATH = "${pkgs.python310}/lib/python3.10/site-packages";
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc
      pkgs.zlib
    ];
    
    # Locale settings
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8";
    
    # Replit specific
    REPLIT_DB_URL = "";
  };
}
