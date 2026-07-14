#!/usr/bin/env bash
set -euo pipefail

if [[ ! -r /proc/sys/fs/binfmt_misc/WSLInterop ]]; then
  echo "error: this bootstrap must run inside WSL 2" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
data_root="${MSF_DATA_DIR:-$HOME/msf-data/Marketing_Swipe_File}"
temp_root="${TMPDIR:-$HOME/.cache/msf/tmp}"

for path in "$repo_root" "$data_root" "$temp_root"; do
  if [[ "$path" == /mnt/* ]]; then
    echo "error: active WSL paths must use the Linux filesystem: $path" >&2
    exit 2
  fi
done

required_commands=(python3 git ffmpeg node npm rsync)
missing=()
for command_name in "${required_commands[@]}"; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    missing+=("$command_name")
  fi
done
if (( ${#missing[@]} )); then
  printf 'error: missing system commands: %s\n' "${missing[*]}" >&2
  echo "install the packages listed in docs/coordination/msf-r20-wsl-default-001-plan.md as root" >&2
  exit 2
fi

mkdir -p "$data_root" "$temp_root"

if [[ ! -x "$repo_root/.venv/bin/python" ]]; then
  python3 -m venv "$repo_root/.venv"
fi

"$repo_root/.venv/bin/python" -m pip install --upgrade pip
"$repo_root/.venv/bin/python" -m pip install -r "$repo_root/requirements-dev.txt"
"$repo_root/.venv/bin/python" -m pip check

cat <<EOF
WSL bootstrap complete.
Repository: $repo_root
Data root: $data_root
Temp root: $temp_root

For the current shell:
  export MSF_DATA_DIR="$data_root"
  export TMPDIR="$temp_root"
EOF
