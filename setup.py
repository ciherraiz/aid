from setuptools import setup, find_packages

setup(
    name='aid',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas>=2.2,<4',
        'jira>=3.8,<4',
        'gspread>=6.0,<7',
        'google-auth>=2.0,<3',
        'google-auth-oauthlib>=1.0,<2',
    ],
    author='flaco',
    description='aid',
    python_requires='>=3.12',
)
