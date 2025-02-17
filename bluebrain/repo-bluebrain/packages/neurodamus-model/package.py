##############################################################################
# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import os
import shutil

import llnl.util.tty as tty

from spack.package import *

from .py_neurodamus import PyNeurodamus
from .sim_model import SimModel, copy_all, make_link

# Definitions
_CORENRN_MODLIST_FNAME = "coreneuron_modlist.txt"
_BUILD_NEURODAMUS_FNAME = "build_neurodamus.sh"
PYNEURODAMUS_DEFAULT_V = PyNeurodamus.LATEST_STABLE
COMMON_DEFAULT_V = "2.8.1"


def version_from_model_ndpy_dep(
    model_v, ndamus_v=PYNEURODAMUS_DEFAULT_V, common_v=COMMON_DEFAULT_V
):
    """New version scheme following dependency on neurodamus-py and common"""
    this_version = model_v + "-" + ndamus_v + "-" + common_v  # e.g. 1.1-3.0.2-2.6.4
    version(this_version, tag=model_v, submodules=True, get_full_repo=True)
    depends_on("py-neurodamus@" + ndamus_v, type=("build", "run"), when="@" + this_version)


class NeurodamusModel(SimModel):
    """An 'abstract' base package for Simulation Models. Therefore no version.
    Eventually in the future Models are independent entities,
    not tied to neurodamus
    """

    # NOTE: Several variants / dependencies come from SimModel
    variant("synapsetool", default=True, description="Enable SynapseTool reader (for edges)")
    variant("mvdtool", default=True, description="Enable MVDTool reader (for nodes)")
    variant(
        "common_mods",
        default="default",
        description="Source of common mods. '': no change, other string: alternate path",
    )

    resource(
        name="common_mods",
        git="ssh://git@bbpgitlab.epfl.ch/hpc/sim/models/common.git",
        tag=COMMON_DEFAULT_V,
        destination="common_latest",
    )

    # Now we depend on neurodamus-py
    # However don't depend on it at runtime just yet, we still want to use
    # use neurodamus-py from GCC stack for compatibility with other Python
    # libs (bglibpy)
    depends_on("py-neurodamus@develop", type=("build", "run"), when="@develop")

    # Note: We dont request link to MPI so that mpicc can do what is best
    # and dont rpath it so we stay dynamic.
    # 'run' mode will load the same mpi module
    depends_on("mpi", type=("build", "run"))

    depends_on("hdf5+mpi")
    depends_on("libsonata-report")
    depends_on("synapsetool+mpi", when="+synapsetool")
    depends_on("py-mvdtool+mpi", type="run", when="+mvdtool")

    # NOTE: With Spack chain we no longer require support for external libs.
    # However, in some setups (notably tests) some libraries might still be
    # specificed as external and, if static,
    # and we must bring their dependencies.
    depends_on("zlib")  # for hdf5

    phases = ["setup_common_mods", "build_model", "merge_hoc_mod", "build", "install"]

    def setup_common_mods(self, spec, prefix):
        """Setup common mod files if provided through variant."""
        # If specified common_mods then we must change the source
        # Particularly useful for CI of changes to models/common
        if spec.variants["common_mods"].value != "default":
            shutil.move("common", "_common_orig")
            force_symlink(spec.variants["common_mods"].value, "common")
        elif spec.satisfies("@1.6:"):
            # From v1.6 on all models require external common
            tty.info("Using Latest common")
            force_symlink("common_latest/common", "common")

    def build_model(self, spec, prefix):
        """Build and install the bare model."""
        self._build_mods("mod")
        # Dont install intermediate src.
        self._install_binaries()

    def merge_hoc_mod(self, spec, prefix):
        """Add hocs, mods and python scripts from neurodamus-core which comes
        as a submodule of py-neurodamus.

        This routine simply adds the additional mods to existing dirs
        so that incremental builds can actually happen.
        """
        core = spec["py-neurodamus"]
        core_prefix = core.prefix

        # If we shall build mods for coreneuron,
        # only bring from core those specified
        if spec.satisfies("+coreneuron"):
            shutil.copytree("mod", "mod_core", True)
            core_nrn_mods = set()
            with open(core_prefix.lib.mod.join(_CORENRN_MODLIST_FNAME)) as core_mods:
                for aux_mod in core_mods:
                    mod_fil = core_prefix.lib.mod.join(aux_mod.strip())
                    if os.path.isfile(mod_fil):
                        shutil.copy(mod_fil, "mod_core")
                        core_nrn_mods.add(aux_mod.strip())
            with working_dir(core_prefix.lib.mod):
                all_mods = set(f for f in os.listdir() if f.endswith(".mod"))
            with open(join_path("mod", "neuron_only_mods.txt"), "w") as blackl:
                blackl.write("\n".join(all_mods - core_nrn_mods) + "\n")

        # Neurodamus model may not have python scripts
        mkdirp("python")

        copy_all(core_prefix.lib.hoc, "hoc", make_link)
        copy_all(core_prefix.lib.mod, "mod", make_link)
        copy_all(core_prefix.lib.python, "python", make_link)

    def build(self, spec, prefix):
        """Build mod files from with nrnivmodl / nrnivmodl-core.
        To support shared libs, nrnivmodl is also passed RPATH flags.
        """
        # NOTE: sim-model now attempts to build all link and
        # include flags from the dependencies
        # link_flag += ' '
        #         + spec['synapsetool'].package.dependency_libs(spec).joined()

        # Create the library with all the mod files as libnrnmech.so/.dylib
        self.mech_name = ""

        if spec.satisfies("+synapsetool"):
            base_include_flag = "-DENABLE_SYNTOOL"
        else:
            base_include_flag = ""

        include_flag, link_flag = self._build_mods("mod", "", base_include_flag, "mod_core")

        # Create rebuild script
        if spec.satisfies("+coreneuron"):
            nrnivmodlcore_call = str(self.nrnivmodl_core_exe)
            for param in self._nrnivmodlcore_params(include_flag, link_flag):
                nrnivmodlcore_call += " '%s'" % param
            include_flag += " " + self._coreneuron_include_flag()
        else:
            nrnivmodlcore_call = ""

        with open(_BUILD_NEURODAMUS_FNAME, "w") as f:
            f.write(
                _BUILD_NEURODAMUS_TPL.format(
                    nrnivmodl=str(which("nrnivmodl")),
                    incflags=include_flag,
                    loadflags=link_flag,
                    nrnivmodlcore_call=nrnivmodlcore_call,
                )
            )
        os.chmod(_BUILD_NEURODAMUS_FNAME, 0o770)

    def install(self, spec, prefix):
        """Install phase.

        bin/ <- special and special-core
        lib/ <- hoc, mod and lib*mech*.so
        share/ <- neuron & coreneuron mod.c's (modc and modc_core)
        python/ If neurodamus-core comes with python, create links
        """
        # base dest dirs already created by model install
        # We install binaries normally, except lib has a suffix
        self._install_binaries()

        # Install mods/hocs, and a builder script
        self._install_src(prefix)
        shutil.move(_BUILD_NEURODAMUS_FNAME, prefix.bin)

        # Create mods links in share
        core = spec["py-neurodamus"]
        force_symlink(core.prefix.lib.mod, prefix.share.mod_neurodamus)
        force_symlink(prefix.lib.mod, prefix.share.mod_full)

        filter_file(
            r"UNKNOWN_NEURODAMUS_MODEL", r"%s" % spec.name, prefix.lib.hoc.join("defvar.hoc")
        )
        filter_file(
            r"UNKNOWN_NEURODAMUS_VERSION", r"%s" % spec.version, prefix.lib.hoc.join("defvar.hoc")
        )

        try:
            commit_hash = self.fetcher[0].get_commit()
        except Exception as e:
            tty.warn(e)
        else:
            filter_file(
                r"UNKNOWN_NEURODAMUS_HASH",
                r"'%s'" % commit_hash[:8],
                prefix.lib.hoc.join("defvar.hoc"),
            )

    def setup_run_environment(self, env):
        self._setup_run_environment_common(env)
        for libnrnmech_name in find(self.prefix.lib, "libnrnmech*", recursive=False):
            # We have the two libs and must export them in different vars
            #  - NRNMECH_LIB_PATH the combined lib (used by neurodamus-py)
            #  - BLUECELLULAB_MOD_LIBRARY_PATH is the pure mechanism
            #        (used by bglib-py)
            if "libnrnmech." in libnrnmech_name:
                env.set("NRNMECH_LIB_PATH", libnrnmech_name)
            else:
                env.set("BLUECELLULAB_MOD_LIBRARY_PATH", libnrnmech_name)


_BUILD_NEURODAMUS_TPL = """#!/bin/sh
set -e
if [ "$#" -eq 0 ]; then
    echo "******* Neurodamus builder *******"
    echo "Syntax:"
    echo "$(basename $0) <mods_dir> [add_include_flags] [add_link_flags]"
    echo
    echo "NOTE: mods_dir is literally passed to nrnivmodl."
    echo "If you only have the mechanism mods"
    echo " and wish to build neurodamus you need to include"
    echo " the neurodamus-specific mods."
    echo " Under \\$NEURODAMUS_ROOT/share you'll find the whole set"
    echo " of original mod files, as"
    echo " well as the neurodamus-specific mods alone."
    echo " You may copy/link them into your directory."
    exit 1
fi

# run with nrnivmodl in path
set -xe

MODDIR=$1
shift

if [ ! -d "$MODDIR" ]; then
    echo "Please provide a valid directory with mod files"
    exit -1
fi

COMPILE_ONLY_NEURON=0

if [[ "$1" == "--only-neuron" ]]; then
    echo "Compiling mechanisms only for NEURON"
    COMPILE_ONLY_NEURON=1
    shift
fi
NRNIVMODL_EXTRA_INCLUDE_FLAGS="$1"
NRNIVMODL_EXTRA_LOAD_FLAGS="$2"

if [ -n "{nrnivmodlcore_call}" ] && [ "$COMPILE_ONLY_NEURON" -eq "0" ]; then
    rm -rf _core_mods
    mkdir _core_mods
    touch "$MODDIR/neuron_only_mods.txt"  # ensure exists
    for f in "$MODDIR"/*.mod; do
        if ! grep $(basename $f) "$MODDIR/neuron_only_mods.txt"; then
            cp $f _core_mods/
        fi
    done
    {nrnivmodlcore_call} _core_mods
    libpath=$(dirname */libcorenrnmech_ext*)
    extra_loadflags="-L $(pwd)/$libpath -lcorenrnmech_ext -Wl,-rpath=\\$ORIGIN"

    echo "Your build supports CoreNeuron. However in some systems
        the coreneuron mods might not be loadable without a location hint.
        In case you get an error such as
            'libcorenrnmech_ext.so: cannot open shared object file
        please run the command:
            export LD_LIBRARY_PATH=$libpath:\\$LD_LIBRARY_PATH"
fi

'{nrnivmodl}' -incflags '{incflags} '"$NRNIVMODL_EXTRA_INCLUDE_FLAGS" -loadflags \
    '{loadflags} '"$extra_loadflags $NRNIVMODL_EXTRA_LOAD_FLAGS" "$MODDIR"

# Final Cleanup
if [ -d _core_mods ]; then
    rm -rf _core_mods
fi
"""
