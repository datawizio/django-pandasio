try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

VERSION = "1.2.0"

setup(
   name="django-pandasio",
   version=VERSION,
   description="Pandas DataFrames in Django",
   license="http://www.gnu.org/copyleft/gpl.html",
   platforms=["any"],
   packages=['pandasio', 'pandasio.db', 'pandasio.validation'],
   package_dir={'pandasio': 'pandasio'},
   install_requires=["six", "pandas", "django==4.2.7", "djangorestframework==3.14.0"],
)
