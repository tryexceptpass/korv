from setuptools import setup, find_packages

setup(
    author = "tryexceptpass",
    author_email = "cmedina@tryexceptpass.org",

    name = "korv",
    version = "0.1.0",
    description = "API framework over SSH",
    long_description="",

    url = "https://github.com/tryexceptpass/korv",

    packages = find_packages(),

    install_requires = [ 'asyncssh' ],

    license = "MIT",
    classifiers = [ 'License :: OSI Approved :: MIT License',

                    'Topic :: Communications',
                    'Topic :: Internet',

                    'Framework :: AsyncIO',

                    'Programming Language :: Python :: 3 :: Only',

                    'Development Status :: 4 - Beta',
                  ],

    keywords = [ 'ssh', 'api', 'framework' ],

)
