from setuptools import setup, find_packages

setup(
    name='russianparser',
    version='0.1',
    packages=find_packages(),
    license='MIT',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>3.5.2',
)