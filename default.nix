with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "impurePythonEnv";

  buildInputs = with python3Packages; [
    click
    hexdump
    prometheus_client
    pyserial
    structlog
  ];
}
