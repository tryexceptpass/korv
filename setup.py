from setuptools import setup, find_packages
from os import path


# Get the long description from the README file
with open(path.join('.', 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    author = "tryexceptpass",
    author_email = "cmedina@tryexceptpass.org",

    name = "korv",
    version = "0.1.0",
    description = "SSH API Frameowrk",
    long_description=long_description,
    long_description_content_type='text/markdown',

    url = "https://github.com/tryexceptpass/korv",

    packages = find_packages(),

    install_requires = ['asyncssh'],
    python_requires='>=3.6',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],

    license = "MIT",
    classifiers = [ 'License :: OSI Approved :: MIT License',

                    'Topic :: Communications',
                    'Topic :: Internet',

                    'Framework :: AsyncIO',

                    'Programming Language :: Python :: 3 :: Only',
                    'Programming Language :: Python :: 3.6',

                    'Development Status :: 4 - Beta',
                  ],

    keywords = 'ssh api framework',

    project_urls={
        'Gitter Chat': 'https://gitter.im/try-except-pass/korv',
        'Say Thanks!': 'https://saythanks.io/to/tryexceptpass',
        'Source': 'https://github.com/tryexceptpass/korv',
        # 'Documentation': 'http://korv.readthedocs.io/en/latest/',
    },
)
