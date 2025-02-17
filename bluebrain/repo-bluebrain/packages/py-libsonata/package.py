# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyLibsonata(PythonPackage):
    """SONATA files reader"""

    homepage = "https://github.com/BlueBrain/libsonata"
    git = "https://github.com/BlueBrain/libsonata.git"
    pypi = "libsonata/libsonata-0.1.14.tar.gz"

    submodules = True

    version("develop", branch="master", get_full_repo=True)
    version("0.1.25", sha256="b332efa718123ee265263e1583a5998eaa945a13b8a22903873764cf1d8173fa")
    version("0.1.24.1", commit="0577eb5142e65363087facb9dc6c12dfd2ae49f2")
    version("0.1.24", sha256="6ec161e3be670025ba3bb5b4f1d1996a1947f094a176a7bcecb466fb3917c58e")
    version("0.1.23", sha256="815aac5bdaa5d025b5f3558ac4d3acb9ebcb070594109af4c0844f47ec701c1d")
    version("0.1.22", sha256="4adbb32ed2fac5d3c74bde03a5e2adb319724d324318a2a7dc2ef3c30f817b2c")
    version("0.1.21", sha256="5b280d82cb21a745d9cdb736c00446e0209494c21d2d17a2c878fabf23a08b68")
    version("0.1.20", sha256="f2e63a26dcf045bb7424e236e12f9b9ef8c46c356e953d26555f313f5763651e")
    version("0.1.18", sha256="1b13728cbffbcb74cc864c7bc186e568945e25c260f732ffa872437c081fd9b4")
    version("0.1.17", sha256="d122dd9fce82c8ce1621746ed9029e7db0d319fb94f6a737fb14f572f632f7b4")
    version("0.1.16", sha256="49ced56992ba8be8aa6638525e8078b7e3ce0d5c05c34ee90746cab02bb5185a")
    version("0.1.15", sha256="8c7c509db692b482cba5b0453579747db5a981ce5b3c13da96b14ae0332a6e81")
    version("0.1.14", sha256="a5c75df1c3ef6fac10d92fb6781643e0834e5c35debe77693686dab8bfcf221f")
    version("0.1.13", sha256="8263938e49b501c477f626b4c25e0c74e91152268830c69aabc96eeb263c6eea")
    version("0.1.12", sha256="f0fa0f3b129d28e41b337ce2c39c3604990752de8e485327ec9df3bf0360e9c1")
    version("0.1.11", sha256="95f302818971fec3f19ef18febd5c31c580490692138c8e4fe3534104d88b5e0")
    version("0.1.10", sha256="7ef9f911f7ea31da5ff5306d8372ec194d223850aede0878ac2a921ce049bbb2")

    depends_on("cmake@3.3:", type="build")
    depends_on("hdf5")
    depends_on("py-pybind11")

    depends_on("py-numpy@1.17:", type=("build", "run"))
    depends_on("py-setuptools", type="build", when="@0.1:")
    depends_on("py-setuptools-scm", type="build", when="@0.1:")

    def patch(self):
        filter_file("EXTLIB_FROM_SUBMODULES", "FALSE", "python/CMakeLists.txt")
