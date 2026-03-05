from setuptools import setup, find_packages

setup(
    name='aid',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'jira',
        'gspread',
        'google-auth',
        'google-auth-oauthlib',
    ],
    author='flaco',
    description='aid',
    python_requires='>=3.12',
)
