from distutils.core import setup

# This is a list of files to install, and where
# (relative to the 'root' dir, where setup.py is)
# You could be more specific.
from setuptools import find_packages
from anki import __author__
from anki import __version__

setup(
    name='anki_tool',
    version=__version__,
    packages=find_packages(),
    py_modules=['command_tool', 'lzo', 'mdict_dir',
                'mdict_query', 'pure_salsa20', "readmdict",
                "ripemd128", "configuration"],
    author=__author__,
    author_email='lazilylamp@gmail.com',
    url='https://github.com/momodae',
    description='A anki word query tool',
    entry_points={
        'console_scripts': [
            'anki = command_tool:main',
        ]
    },
    classifiers=[
            "Programming Language :: Python :: 3.5",
        ],
    zip_safe=False,
    install_requires=['requests']
)
