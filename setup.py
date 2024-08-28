from setuptools import setup, find_packages


def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name='opentouch-interface',
    version='0.1.2',
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
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
