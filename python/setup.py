from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os
import shutil

# Copy csrc files into the build tree so paths stay relative
here = os.path.abspath(os.path.dirname(__file__))
csrc_src = os.path.join(here, "..", "csrc")
csrc_dst = os.path.join(here, "src", "semanticsmith", "_csrc")
os.makedirs(csrc_dst, exist_ok=True)
for fname in ["ssw_core.c", "ssw_core.h"]:
    shutil.copy2(os.path.join(csrc_src, fname), os.path.join(csrc_dst, fname))

extensions = [
    Extension(
        "semanticsmith._core",
        sources=[
            os.path.join("src", "semanticsmith", "_core.pyx"),
            os.path.join("src", "semanticsmith", "_csrc", "ssw_core.c"),
        ],
        include_dirs=[
            os.path.join("src", "semanticsmith", "_csrc"),
            np.get_include(),
        ],
        language="c",
    )
]

setup(
    ext_modules=cythonize(extensions, language_level="3"),
)
