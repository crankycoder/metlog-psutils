# ***** BEGIN LICENSE BLOCK *****
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2012
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Rob Miller (rmiller@mozilla.com)
#   Victor Ng (vng@mozilla.com)
#
# ***** END LICENSE BLOCK *****
import os
from setuptools import setup, find_packages

version = '0.1'

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

setup(name='metlog-psutils',
      version=version,
      description="PSUtils extensions to metrics logging",
      long_description=README,
      classifiers=[
          'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
          ],
      keywords='metlog metrics logging client',
      author='Victor Ng',
      author_email='vng@mozilla.com',
      url='https://github.com/mozilla-services/metlog-psutils',
      license='MPLv2.0',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          ],
      extras_require={
          },
      tests_require=[
          'nose',
          'mock',
          ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
