import os
import sys
import ctypes
import ctypes.wintypes
from typing import Optional


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


_CLSID_FileOpenDialog = _GUID(
    0xDC1C5A9C, 0xE88A, 0x4DDE, (ctypes.c_ubyte * 8)(0xA5, 0xA1, 0x60, 0xF8, 0x2A, 0x20, 0xAE, 0xF7)
)
_IID_IFileOpenDialog = _GUID(
    0xD57C7288, 0xD4AD, 0x4768, (ctypes.c_ubyte * 8)(0xBE, 0x02, 0x9D, 0x96, 0x95, 0x32, 0xD9, 0x60)
)
_IID_IShellItem = _GUID(
    0x43826D1E, 0xE718, 0x42EE, (ctypes.c_ubyte * 8)(0xBC, 0x55, 0xA1, 0xE2, 0x61, 0xC3, 0x7B, 0xFE)
)

FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
SIGDN_FILESYSPATH = 0x80058000

_ole32 = ctypes.windll.ole32
_shell32 = ctypes.windll.shell32


def _com_release(p):
    if p:
        vtable = ctypes.cast(p, ctypes.POINTER(ctypes.c_void_p))[0]
        release = ctypes.cast(
            ctypes.cast(vtable, ctypes.POINTER(ctypes.c_void_p))[2],
            ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p),
        )
        release(p)


def _get_vtable_method(vtable, index, restype, *argtypes):
    return ctypes.WINFUNCTYPE(restype, *argtypes)(vtable[index])


def pick_folder(title: str = "Select Folder", hwnd: int = 0, start_dir: str = "") -> Optional[str]:
    """Open native Windows folder picker without FOS_FORCEFILESYSTEM.

    Uses IFileOpenDialog with FOS_PICKFOLDERS but without the FOS_FORCEFILESYSTEM
    flag that normally hides the WSL Linux node in the sidebar.

    Returns the selected folder path, or None if cancelled or unavailable.
    """
    if os.name != "nt":
        return None

    pDialog = ctypes.c_void_p()
    hr = _ole32.CoCreateInstance(
        ctypes.byref(_CLSID_FileOpenDialog),
        None,
        1,
        ctypes.byref(_IID_IFileOpenDialog),
        ctypes.byref(pDialog),
    )
    if hr != 0:
        return None

    vtable_ptr = ctypes.cast(pDialog, ctypes.POINTER(ctypes.c_void_p))[0]
    vtable = ctypes.cast(
        vtable_ptr,
        ctypes.POINTER(ctypes.c_void_p * 28),
    ).contents

    try:
        GetOptions = _get_vtable_method(vtable, 10, ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint))
        SetOptions = _get_vtable_method(vtable, 9, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint)
        SetTitle = _get_vtable_method(vtable, 17, ctypes.c_long, ctypes.c_void_p, ctypes.wintypes.LPCWSTR)

        opts = ctypes.c_uint()
        GetOptions(pDialog, ctypes.byref(opts))
        SetOptions(pDialog, opts.value | FOS_PICKFOLDERS)

        SetTitle(pDialog, title)

        if start_dir and os.path.isdir(start_dir):
            SetFolder = _get_vtable_method(vtable, 12, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)
            pStartItem = ctypes.c_void_p()
            hr = _shell32.SHCreateItemFromParsingName(
                ctypes.wintypes.LPCWSTR(start_dir),
                None,
                ctypes.byref(_IID_IShellItem),
                ctypes.byref(pStartItem),
            )
            if hr == 0 and pStartItem:
                SetFolder(pDialog, pStartItem)
                _com_release(pStartItem)

        Show = _get_vtable_method(vtable, 3, ctypes.c_long, ctypes.c_void_p, ctypes.wintypes.HWND)
        hr = Show(pDialog, hwnd)
        if hr != 0:
            return None

        GetResult = _get_vtable_method(vtable, 20, ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
        pItem = ctypes.c_void_p()
        hr = GetResult(pDialog, ctypes.byref(pItem))
        if hr != 0 or not pItem:
            return None

        try:
            item_vtable_ptr = ctypes.cast(pItem, ctypes.POINTER(ctypes.c_void_p))[0]
            item_vtable = ctypes.cast(
                item_vtable_ptr,
                ctypes.POINTER(ctypes.c_void_p * 6),
            ).contents

            GetDisplayName = _get_vtable_method(
                item_vtable, 5, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.wintypes.LPWSTR)
            )

            path_ptr = ctypes.wintypes.LPWSTR()
            hr = GetDisplayName(pItem, SIGDN_FILESYSPATH, ctypes.byref(path_ptr))
            if hr == 0 and path_ptr and path_ptr.value:
                path = path_ptr.value
                _ole32.CoTaskMemFree(path_ptr)
                if os.path.isdir(path):
                    return path
            return None
        finally:
            _com_release(pItem)
    finally:
        _com_release(pDialog)


def get_existing_directory(parent=None, caption="", directory="", options=None):
    """Drop-in replacement for QFileDialog.getExistingDirectory with WSL support.

    On Windows, opens a native IFileOpenDialog without FOS_FORCEFILESYSTEM so
    the WSL Linux node is visible in the sidebar. On non-Windows, delegates
    directly to QFileDialog.

    Returns the selected directory path, or empty string if cancelled.
    """
    if os.name == "nt":
        from PyQt6.QtWidgets import QWidget
        hwnd = int(parent.winId()) if isinstance(parent, QWidget) and parent else 0
        path = pick_folder(caption or "Select Folder", hwnd, directory)
        return path or ""
    from PyQt6.QtWidgets import QFileDialog
    return QFileDialog.getExistingDirectory(parent, caption, directory, options or QFileDialog.Option.ShowDirsOnly)
