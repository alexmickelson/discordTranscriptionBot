{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    pkgs.pipx
    pkgs.gemini-cli
  ];
  shellHook = ''
    export PIPX_HOME=$(pwd)/.pipx
    export PIPX_BIN_DIR=$(pwd)/.pipx/bin
    export PATH="$PATH:$(pwd)/.pipx/bin"
    pipx install uv
  '';
}