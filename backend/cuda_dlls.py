"""
Windows CUDA/cuDNN DLL path setup for ONNX Runtime pip NVIDIA packages.
"""
import os
import site
from pathlib import Path
from typing import List


_ADDED_DLL_DIRS = []


def prepare_cuda_dll_paths() -> List[str]:
    """
    Add NVIDIA pip package DLL folders to the Windows loader search path.

    Packages such as nvidia-cudnn-cu12 install DLLs under:
    Lib/site-packages/nvidia/<package>/bin
    Windows does not always discover those folders during CUDA EP execution.
    """
    added = []
    if os.name != "nt":
        return added

    candidates = []
    for base in site.getsitepackages():
        nvidia_dir = Path(base) / "nvidia"
        if not nvidia_dir.exists():
            continue

        candidates.extend(sorted(nvidia_dir.glob("*/bin")))

    existing_path = os.environ.get("PATH", "")
    path_parts = existing_path.split(os.pathsep) if existing_path else []

    for directory in candidates:
        if not directory.exists():
            continue

        directory_str = str(directory)
        if directory_str not in path_parts:
            os.environ["PATH"] = directory_str + os.pathsep + os.environ.get("PATH", "")
            path_parts.insert(0, directory_str)

        try:
            handle = os.add_dll_directory(directory_str)
            _ADDED_DLL_DIRS.append(handle)
            added.append(directory_str)
        except (FileNotFoundError, OSError):
            pass

    return added
