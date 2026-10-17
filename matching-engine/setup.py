from setuptools import Extension, setup
from Cython.Build import cythonize

setup(
    name="chronosmatch-engine",
    ext_modules=cythonize(
        [Extension("chronosmatch.engine", ["chronosmatch/engine.pyx"])],
        compiler_directives={"language_level": 3},
    ),
    packages=["chronosmatch"],
    zip_safe=False,
)
