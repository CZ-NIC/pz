from pathlib import Path

from setuptools import setup

# load long description
p = Path("README.md")
long_description = p.read_text() if p.exists() else None

setup(
    name='pz',
    version='1.0.0',
    author='Edvard Rejthar',
    author_email='edvard.rejthar@nic.cz',
    url='https://github.com/CZ-NIC/pz',
    license='GNU GPLv3',
    description='Ever wished to use the Python syntax to work in Bash?'
                ' Then pythonize it, piping the contents through your tiny Python script with `pz` utility!',
    long_description=long_description,
    long_description_content_type="text/markdown",
    scripts=['pz'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Text Processing',
        'Topic :: Utilities'
    ],
    python_requires='>=3.6',
)
