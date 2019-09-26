from setuptools import setup, find_packages

setup(
    name='koursaros',
    packages=find_packages() + ['*.koursaros/*'],
    version='0.0.1',
    license='MIT',
    description='Koursaros is a distributed, cloud-'
                'native platform for developing and deploying '
                'automated information retrieval and inference applications.',
    author='Koursaros',
    author_email='cole.thienes@gmail.com',
    url='https://github.com/koursaros-ai/koursaros',
    # download_url='https://github.com/koursaros-ai/koursaros/archive/0.0.1.tar.gz',
    keywords=['koursaros', 'distributed', 'cloud-native', 'neural', 'inference'],
    install_requires=[
        'pika',
    ],
    entry_points={
        'console_scripts': [
            'kctl = kctl.__main__:main',
        ],
    },
    classifiers=[
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
