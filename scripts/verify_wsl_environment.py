"""Backward-compatible import path for the retired WSL-only verifier."""

from scripts.verify_gold_runtime import default_temp_root, inside_wsl, main, path_check, selected_runtime, verify_environment

__all__ = [
    "default_temp_root",
    "inside_wsl",
    "main",
    "path_check",
    "selected_runtime",
    "verify_environment",
]


if __name__ == "__main__":
    raise SystemExit(main())
