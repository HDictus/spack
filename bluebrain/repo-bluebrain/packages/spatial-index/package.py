# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
from spack.package import *


class SpatialIndex(PythonPackage):
    """Spatial indexer for geometries and morphologies"""

    homepage = "https://bbpgitlab.epfl.ch/hpc/spatial-index"
    git = "ssh://git@bbpgitlab.epfl.ch/hpc/spatial-index.git"
    url = "ssh://git@bbpgitlab.epfl.ch/hpc/spatial-index.git"

    submodules = True

    version("develop", branch="main")
    version("2.1.0", tag="2.1.0")
    version("2.0.0", tag="2.0.0")
    version("1.2.1", tag="1.2.1")
    version("1.2.0", tag="1.2.0")
    version("1.1.0", tag="1.1.0")
    version("1.0.0", tag="1.0.0")
    version("0.9.0", tag="0.9.0")
    version("0.8.3", tag="0.8.3")
    version("0.8.2", tag="0.8.2")
    version("0.8.1", tag="0.8.1")
    version("0.8.0", tag="0.8.0")
    version("0.7.0", tag="0.7.0")
    version("0.6.0", tag="0.6.0")

    depends_on("py-setuptools")
    depends_on("cmake@3.2:", type="build")
    depends_on("boost@1.79.0: +filesystem+serialization")
    depends_on("py-docopt", type=("build", "run"))
    # `py-libsonata@0.1.15` contains a regression that throws
    # on empty selections. Therefore, SpatialIndex can't use
    # that version of `py-libsonata`. See,
    #  https://github.com/BlueBrain/libsonata/pull/232
    depends_on("py-libsonata", type=("build", "run"), when="@0.2.2:")
    conflicts("py-libsonata@0.1.15")
    depends_on("py-morphio", type=("build", "run"), when="@:2.0.0")
    depends_on("py-morphio@3.3.5:", type=("build", "run"), when="@2.1.0:")
    depends_on("py-morpho-kit", type=("build", "run"), when="@:0.8.3")
    depends_on("py-mvdtool~mpi", type=("build", "run"), when="@:0.8.3")
    depends_on("py-numpy-quaternion", type=("build", "run"))
    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-tqdm", type=("build", "run"))

    depends_on("mpi", when="@0.5.2:")
    depends_on("py-mpi4py", type=("build", "run"))

    @run_after("install")
    def install_headers(self):
        install_tree("include", self.prefix.include)
