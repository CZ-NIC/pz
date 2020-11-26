from pathlib import Path

from setuptools import setup

# load long description
p = Path("README.md")
if p.exists():
    long_description = p.read_text()

setup(
    name='pyed',
    version='0.9rc1',
    author='Edvard Rejthar',
    author_email='edvard.rejthar@nic.cz',
    url='https://github.com/CZ-NIC/pyed',
    license='GNU GPLv3',
    description='Ever wished to use the Python syntax to work in Bash?'
                ' Then do it and pipe the contents through your tiny Python script with `pyed` utility!',
    long_description=long_description,
    long_description_content_type="text/markdown",
    scripts=['pyed'],
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    python_requires='>=3.6',
)
