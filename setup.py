# -*- coding: utf-8 -*
from setuptools.command.install import install
from setuptools import find_packages
from setuptools import setup
from sys import version_info, stderr, exit
import codecs
import sys
import os


def read(*parts):
    # intentionally *not* adding an encoding option to open
    # see here: https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts), 'r').read()


setup(name="hitchtrigger",
      version=read('VERSION').replace('\n', ''),
      description="Build tool to selectively run blocks of build commands under specified conditions",
      long_description=read('README.rst'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Topic :: Text Processing :: Markup',
          'Topic :: Software Development :: Libraries',
          'Natural Language :: English',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='test build',
      author='Colm O\'Connor',
      author_email='colm.oconnor.github@gmail.com',
      url='https://github.com/hitchtest/hitchtrigger',
      license='MIT',
      install_requires=['peewee>=2.1.0', 'humanize>=0.5.1', ],
      packages=find_packages(exclude=["tests", ]),
      package_data={},
      zip_safe=False,
      include_package_data=True,
)
