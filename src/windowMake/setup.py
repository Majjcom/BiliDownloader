from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Window',
    version='1.0.0',
    url='http://www.majjcom.site:12568/',
    author='Majjcom',
    ext_modules=cythonize("window.py"),
    zip_safe=False,
)