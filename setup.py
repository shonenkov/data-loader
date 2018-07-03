# -*- coding: utf-8 -*-
import os
import sys
import re
from setuptools import setup
from setuptools.command.test import test


tests_require = ['pytest==3.2.3', 'pytest-cov==2.5.1', 'coverage == 4.5.1', 'coveralls == 1.3.0']


class PyTest(test):

    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        test.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def read(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        file_content = f.read()
    return file_content


def get_requirements():
    requirements = []
    for requirement in read('requirements.txt').splitlines():
        if requirement.startswith('git+') or requirement.startswith('svn+') or requirement.startswith('hg+'):
            parsed_requires = re.findall(r'#egg=([\w\d\.]+)-([\d\.]+)$', requirement)
            if parsed_requires:
                package, version = parsed_requires[0]
                requirements.append(f'{package}=={version}')
            else:
                print('WARNING! For correct matching dependency links need to specify package name and version'
                      'such as <dependency url>#egg=<package_name>-<version>')
        else:
            requirements.append(requirement)
    return requirements


def get_links():
    return [
        requirement for requirement in read('requirements.txt').splitlines()
        if requirement.startswith('git+') or requirement.startswith('svn+') or requirement.startswith('hg+')
    ]


def get_version():
    """ Get version from the package without actually importing it. """
    init = read('data_loader/__init__.py')
    for line in init.split('\n'):
        if line.startswith('__version__'):
            return eval(line.split('=')[1])


setup(
    name='data-loader',
    version=get_version(),
    author='Aleksei Shonenkov',
    author_email='shonenkov@phystech.edu',
    description='Data loader.',
    packages=['data_loader'],
    cmdclass={'test': PyTest},
    tests_require=tests_require,
    install_requires=get_requirements(),
    dependency_links=get_links(),
    long_description=read('README.md'),
)
