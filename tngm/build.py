from distutils.core import setup
from distutils.extension import Extension
import numpy as np
from Cython.Distutils import build_ext
import os
import sysconfig

try:
    numpy_include = np.get_include()
except AttributeError:
    numpy_include = np.get_numpy_include()


from Cython.Distutils import build_ext


def get_ext_filename_without_platform_suffix(filename):
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')

    if ext_suffix == ext:
        return filename

    ext_suffix = ext_suffix.replace(ext, '')
    idx = name.find(ext_suffix)

    if idx == -1:
        return filename
    else:
        return name[:idx] + ext


class BuildExtWithoutPlatformSuffix(build_ext):
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        return get_ext_filename_without_platform_suffix(filename)

ext_modules = [
    Extension(
            "lib.sample",
            ["sample.pyx"],
            # extra_compile_args={'gcc': ["-Wno-cpp", "-Wno-unused-function"]},
            include_dirs=[numpy_include]
        ),
]

setup(
    name="Sample",
    ext_modules=ext_modules,
    # inject our custom trigger
    cmdclass={'build_ext': BuildExtWithoutPlatformSuffix},
)