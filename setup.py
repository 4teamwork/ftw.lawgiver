import os
from setuptools import setup, find_packages


version = '2.0.0.dev0'


tests_require = [
    'ftw.builder',
    'ftw.testbrowser',
    'ftw.testing',
    'plone.api',
    'plone.restapi',
    'plone.testing',
]


extras_require = {
    'tests': tests_require,
}


setup(name='ftw.lawgiver',
      version=version,
      description='Generate your Plone workflows by describing it in' +
      ' plain text with a DSL.',

      long_description=open('README.rst').read() + '\n' +
      open(os.path.join('docs', 'HISTORY.txt')).read(),

      classifiers=[
          "Development Status :: 3 - Alpha",
          "Environment :: Web Environment",
          "Framework :: Plone",
          "Framework :: Plone :: 6.0",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.9",
      ],

      keywords='ftw lawgiver generate workflows dsl',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.lawgiver',

      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw', ],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'Plone',
          'argparse',
          'ftw.upgrade',
          'path.py',
          'setuptools',
          'i18ndude>=5.4.2',
      ],

      tests_require=tests_require,
      extras_require=extras_require,

      entry_points="""
      # -*- Entry points: -*-
      [plone.autoinclude.plugin]
      target = plone

      [zopectl.command]
      rebuild_workflows = ftw.lawgiver.commands:rebuild_workflows
      """,
      )
