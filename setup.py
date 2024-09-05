import os
from setuptools import setup, find_packages


def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Determine the version number
if os.getenv('GITHUB_REF') and os.getenv('GITHUB_REF').startswith('refs/tags/'):
    # Use the version from the tag (assuming the tag is the version number)
    version = os.getenv('GITHUB_REF').split('/')[-1]
else:
    # Use a development version based on the run number for TestPyPI
    version = f"0.1.dev{os.getenv('GITHUB_RUN_NUMBER')}"

setup(
    name='opentouch-interface',
    version=version,
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'opentouch-dashboard = opentouch_interface.dashboard.start:main'
        ],
    },
    author='Roberto Calandra',
    author_email='rcalandra@lasr.org',
    description='Interface to connect to touch sensors',
    python_requires='>=3.11',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lasr-lab/opentouch-interface',
    classifiers=[
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
