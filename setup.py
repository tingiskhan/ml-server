from setuptools import setup, find_packages
import os

NAME = 'pylurch'


def _get_version():
    folder = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(folder, f'{NAME}/__init__.py'), 'r') as f:
        versionline = next(line for line in f.readlines() if line.strip().startswith('__version__'))
        version = versionline.split('=')[-1].strip().replace('\'', '')

    return version


setup(
    name=NAME,
    version=_get_version(),
    author='Victor Gruselius',
    author_email='victor.gruselius@gmail.com',
    description='Library for serving machine learning models',
    packages=find_packages(exclude='example'),
    install_requires=[
        'sqlalchemy',
        'falcon',
        'pandas',
        'pandas',
        'numpy',
        'scikit-learn',
        'onnx',
        'onnxruntime',
        'skl2onnx',
        'dill',
        'pyyaml',
        'marshmallow',
        'marshmallow-enum',
        'marshmallow-sqlalchemy',
        'dateparser',
        'rq',
        'cachetools'
    ]
)