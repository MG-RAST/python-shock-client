import os
import sys
from setuptools import setup
import ShockClient

requirements = []
if sys.version_info < (2, 7):
    requirements.append('argparse>=1.2.1')
requirements.append('PrettyTable>=0.5')
requirements.append('progressbar>=2.2')

setup(
    name='ShockClient',
    version=ShockClient.__version__,
    description=ShockClient.__doc__.strip(),
    download_url='https://github.com/MG-RAST/ShockClient',
    author=ShockClient.__author__,
    license=ShockClient.__licence__,
    packages=['ShockClient'],
    entry_points={
        'console_scripts': [
            'shock = ShockClient.__main__:main',
        ],
    },
    install_requires=requirements,
    classifiers=[],
)