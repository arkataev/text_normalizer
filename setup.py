from setuptools import setup, find_packages

setup(
    name='text_normalizer',
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        'version_scheme': 'python-simplified-semver',
        'local_scheme': 'no-local-version',
    },
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    license='MIT license',
    author='Alexander Kataev',
    author_email='arkataev@gmail.com',
    description='text normalization tools',
    python_requires='>=3.6',
    setup_requires=['setuptools_scm'],
    install_requires=['nltk==3.5.*', 'pymystem3==0.2.0'],
    include_package_data=True,
    platforms=["POSIX"],
    package_data={
        '': ['data']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ],
    keywords=['nlp', 'text normalization', 'tokenization', 'morphology analysis', 'stemming', 'word2num']
)
