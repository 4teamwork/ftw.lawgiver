import os
from setuptools import setup, find_packages


version = '1.0.dev0'


tests_require = [

    'Products.CMFCore',
    'ftw.testing',
    'plone.app.testing',
    'unittest2',
    'z3c.autoinclude',
    'zope.configuration',

    ]


setup(name='ftw.lawgiver',
      version=version,
      description='Generate your Plone workflows by describing it in' + \
          ' plain text with a DSL.',

      long_description=open('README.rst').read() + '\n' + \
          open(os.path.join('docs', 'HISTORY.txt')).read(),

      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

      keywords='ftw lawgiver generate workflows dsl',
      author='4teamwork GmbH',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.lawgiver',

      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw', ],
      include_package_data=True,
      zip_safe=False,

      install_requires=[

        'Products.GenericSetup',
        'lxml',
        'plone.i18n',
        'setuptools',
        'zope.component',
        'zope.configuration',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.schema',
        'zope.security',

        ],

      tests_require=tests_require,
      extras_require=dict(tests=tests_require),

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
