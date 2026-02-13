from setuptools import setup, find_packages

setup(
    name='aid',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.3.0',
    ],
    author='flaco',
    description='aid',
    python_requires='>=3.12',
)
