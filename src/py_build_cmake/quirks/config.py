import configparser
import os
import platform
import sys
import sysconfig
import warnings
from typing import Optional, Union, List
from ..config_options import ConfigNode, pth


def platform_to_platform_tag(plat: str) -> str:
    """https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#platform-tag"""
    return plat.replace('.', '_').replace('-', '_')


def get_python_lib_impl(libdir: str):
    """Return the path to python<major><minor>.lib or
    python<major>.lib if it exists in libdir. None otherwise."""
    v = sys.version_info
    python3xlib = os.path.join(libdir, f'python{v.major}{v.minor}.lib')
    if os.path.exists(python3xlib):
        return python3xlib
    python3lib = os.path.join(libdir, f'python{v.major}.lib')
    if os.path.exists(python3lib):
        return python3lib
    return None


def get_python_lib(
        library_dirs: Optional[Union[str, List[str]]]) -> Optional[str]:
    """Return the path the the first python<major><minor>.lib or
    python<major>.lib file in any of the library_dirs.
    Returns None if no such file exists."""
    if library_dirs is None:
        return None
    if isinstance(library_dirs, str):
        library_dirs = [library_dirs]
    not_none = lambda x: x is not None
    try:
        return next(filter(not_none, map(get_python_lib_impl, library_dirs)))
    except StopIteration:
        return None


def cross_compile_win(config, plat_name, library_dirs, cmake_platform):
    warnings.warn(
        f"DIST_EXTRA_CONFIG.build_ext specified plat_name that is different from the current platform. Automatically enabling cross-compilation for {cmake_platform}"
    )
    assert not config.contains('cross')
    cross_cfg = {
        'os': 'windows',
        'toolchain_file': '',
        'arch': platform_to_platform_tag(plat_name),
        'cmake': {
            'options': {
                'CMAKE_SYSTEM_NAME': 'Windows',
                'CMAKE_SYSTEM_PROCESSOR': cmake_platform,
                'CMAKE_GENERATOR_PLATFORM': cmake_platform,
            }
        },
    }
    python_lib = get_python_lib(library_dirs)
    if python_lib is not None:
        cross_cfg['library'] = python_lib
        python_root = os.path.dirname(os.path.dirname(python_lib))
        if os.path.exists(os.path.join(python_root, 'include')):
            cross_cfg['root'] = python_root
    else:
        warnings.warn(
            "Python library was not found in DIST_EXTRA_CONFIG.build_ext.library_dirs."
        )
    config.setdefault(pth('cross'), ConfigNode.from_dict(cross_cfg))


def handle_cross_win(config: ConfigNode, plat_name: str,
                     library_dirs: Optional[Union[str, List[str]]]):
    cmake_platform = {
        'win32': 'x86',
        'win-amd64': 'x64',
        'win-arm32': 'arm',
        'win-arm64': 'arm64',
    }.get(plat_name)
    if cmake_platform is not None:
        cross_compile_win(config, plat_name, library_dirs, cmake_platform)


def handle_dist_extra_config_win(config: ConfigNode, dist_extra_conf: str):
    distcfg = configparser.ConfigParser()
    distcfg.read(dist_extra_conf)

    library_dirs = distcfg.get('build_ext', 'library_dirs', fallback='')
    plat_name = distcfg.get('build_ext', 'plat_name', fallback='')

    if plat_name and plat_name != sysconfig.get_platform():
        handle_cross_win(config, plat_name, library_dirs)


def config_quirks_win(config: ConfigNode):
    dist_extra_conf = os.getenv('DIST_EXTRA_CONFIG')
    if dist_extra_conf is not None:
        if config.contains('cross'):
            warnings.warn(
                "Cross-compilation configuration was not empty, so I'm ignoring DIST_EXTRA_CONFIG"
            )
        elif not config.contains('cmake'):
            warnings.warn(
                "CMake configuration was empty, so I'm ignoring DIST_EXTRA_CONFIG"
            )
        else:
            handle_dist_extra_config_win(config, dist_extra_conf)


def config_quirks(config: ConfigNode):
    dispatch = {"Windows": config_quirks_win}.get(platform.system())
    if dispatch is not None:
        dispatch(config)
