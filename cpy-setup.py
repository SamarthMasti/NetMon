from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        ["PollerEngine.py", "ApFlashVulnerableChecker.py"],
        compiler_directives={"language_level": "3"}
    )
)