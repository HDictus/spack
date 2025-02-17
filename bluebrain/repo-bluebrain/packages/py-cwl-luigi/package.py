# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyCwlLuigi(PythonPackage):
    """Luigi wrapper for CWL workflows"""

    homepage = "https://bbpgitlab.epfl.ch/nse/cwl-luigi"
    git = "ssh://git@bbpgitlab.epfl.ch/nse/cwl-luigi.git"

    version("develop", branch="main")
    version("0.3.1", tag="cwl-luigi-v0.3.1")

    depends_on("python@3.9:", type=("build", "run"))

    depends_on("py-setuptools", type=("build", "run"))

    depends_on("py-click@8.0:", type=("build", "run"))
    depends_on("py-jsonschema@3.0:", type=("build", "run"))
    depends_on("py-luigi@3.0:", type=("build", "run"))
    depends_on("py-pyyaml@6.0:", type=("build", "run"))
    depends_on("py-nexusforge@0.8.0:", type=("build", "run"))

    @run_after("install")
    @on_package_attributes(run_tests=True)
    def test_install(self):
        python("-m", "pytest", "tests")
