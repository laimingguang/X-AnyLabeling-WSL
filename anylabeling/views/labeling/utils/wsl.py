import os
import os.path as osp
import subprocess


def get_wsl2_distro_paths():
    try:
        output = subprocess.run(
            ["wsl", "-l", "-v"],
            capture_output=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return []

    raw = output.stdout.decode("utf-16-le", errors="replace")
    distro_paths = []
    for line in raw.strip().splitlines():
        line = line.strip().rstrip("\0")
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        version = parts[-1]
        if version != "2":
            continue
        name_start = 1 if parts[0] == "*" else 0
        name = " ".join(parts[name_start:-2])
        if name:
            distro_paths.append(rf"\\wsl.localhost\{name}")
    return distro_paths


def is_user_distro(path, name):
    """Check if a WSL distro is a user-accessible distro.

    A distro is considered a user distro if it has a non-empty /home
    directory, OR if its name does not contain 'docker' (to allow
    root-only distros like Alpine while hiding docker internals).
    """
    home_path = osp.join(path, "home")
    if osp.isdir(home_path) and os.listdir(home_path):
        return True
    return "docker" not in name.lower()


def list_directory_entries(path):
    """List subdirectory names under *path*, or None if the path cannot be read.

    Returns:
        list[str] | None: Sorted subdirectory names, or None on OSError.
    """
    try:
        entries = sorted(os.listdir(path))
    except OSError:
        return None
    return [e for e in entries if osp.isdir(osp.join(path, e))]
