from Cython.Build import cythonize
from setuptools import Extension, setup

extensions = [
    Extension(
        "kolmogorov_complexity_estimator.native.encoder",
        ["kolmogorov_complexity_estimator/native/encoder.pyx"],
    ),
    Extension(
        "kolmogorov_complexity_estimator.native.tm_ext",
        ["kolmogorov_complexity_estimator/native/turing_machine_ext.pyx"],
    ),
]

setup(
    name="KolmogorovComplexityEstimatorPythonPackage",
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
)
