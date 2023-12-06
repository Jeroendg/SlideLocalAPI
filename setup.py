'''
Install Slide Local API
'''

import setuptools

with open('README.pypi') as f:
    LONG_DESCRIPTION = f.read()

setuptools.setup(
    name='SlideLocalAPI',
    version='0.2.2',
    url='https://github.com/Jeroendg/SlideLocalAPI/',
    license='GPL-3.0',
    author='Jeroen De Gendt',
    author_email='jeroen@degendt.xyz',
    description='Python API to utilise the Slide Local API',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    install_requires=['aiohttp'],
    python_requires='>=3.5.2',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: GPL-3.0',
        'Operating System :: OS Independent',
    ],
)
