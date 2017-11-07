from setuptools import find_packages, setup

package = 'genbank-qc'
version = '0.1a1'

setup(name=package,
      version=version,
      license="MIT",
      url="https://github.com/andrewsanchez/genbank-qc",
      description="Automated quality control for Genbank genomes.",
      author='Andrew Sanchez',
      author_email='inbox.asanchez@gmail.com',
      keywords='NCBI bioinformatics',
      packages=find_packages(),
      include_package_date=True,
      install_requires=[
          'click',
          'numpy',
          'pandas',
          'scikit-bio',
          'biopython'],
      entry_points='''
      [console_scripts]
      genbank-qc=genbank_qc.__main__:cli
      ''',
      classifiers=[
            'Topic :: Scientific/Engineering :: Bio-Informatics',
            'Programming Language :: Python :: 3.6',
            'Operating System :: POSIX :: Linux',
            'License :: OSI Approved :: MIT License',
            'Intended Audience :: Science/Research',
            'Environment :: Console',
            'Development Status :: 3 - Alpha'])
