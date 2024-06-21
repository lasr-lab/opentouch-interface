from setuptools import setup, find_packages

setup(
    name='opentouch_interface',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'streamlit'
    ],
    author='Roberto Calandra',
    author_email='rcalandra@lasr.org',
    description='Description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lasr-lab/opentouch-interface',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
