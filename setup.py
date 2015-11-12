try:
    from setuptools import setup
    setuptools_available = True
except ImportError:
    from distutils.core import setup
    setuptools_available = False

params = {}

if setuptools_available:
    params['entry_points'] = {'console_scripts': ['font-dl = font_dl:main']}
else:
    params['scripts'] = ['bin/font-dl']

setup(name='font_dl',
      version='0.1',
      description='Web fonts downloader',
      license='MIT',
      long_description='Small program to get webfonts embedded in CSS files'
      ' of a webpage. It is the responsibility of the user to check the EULA'
      ' of each downloaded font.',
      url='https://github.com/xoolive/font-dl',
      author='Xavier Olive',
      packages=['font_dl',],
      **params
)
