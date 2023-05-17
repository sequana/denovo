#
#  This file is part of Sequana software
#
#  Copyright (c) 2016-2021 - Sequana Development Team
#
#  Distributed under the terms of the 3-clause BSD license.
#  The full license is in the LICENSE file, distributed with this software.
#
#  website: https://github.com/sequana/sequana
#  documentation: http://sequana.readthedocs.io
#
##############################################################################
import sys
import os
import argparse

from sequana_pipetools.options import *
from sequana_pipetools.options import before_pipeline
from sequana_pipetools.misc import Colors
from sequana_pipetools.info import sequana_epilog, sequana_prolog
from sequana_pipetools import SequanaManager

col = Colors()

NAME = "denovo"


class Options(argparse.ArgumentParser):
    def __init__(self, prog=NAME, epilog=None):
        usage = col.purple(sequana_prolog.format(**{"name": NAME}))
        super(Options, self).__init__(
            usage=usage,
            prog=prog,
            description="",
            epilog=epilog,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # add a new group of options to the parser
        so = SlurmOptions(memory=8000, profile="local")
        so.add_options(self)

        # add a snakemake group of options to the parser
        so = SnakemakeOptions(working_directory=NAME)
        so.add_options(self)

        # add a data group of options to the parser
        so = InputOptions()
        so.add_options(self)

        so = GeneralOptions()
        so.add_options(self)

        pipeline_group = self.add_argument_group("pipeline")
        pipeline_group.add_argument("--quast-reference", default=None, type=str)

        pipeline_group = self.add_argument_group("section_prokka")
        pipeline_group.add_argument("--skip-prokka", action="store_true")
        pipeline_group.add_argument(
            "--prokka-kingdom", default="Bacteria", type=str, choices=["Archaea", "Mitochondria", "Viruses", "Bacteria"]
        )

        pipeline_group = self.add_argument_group("section_sequana_coverage")
        pipeline_group.add_argument("--sequana-coverage-circular", action="store_true")

        pipeline_group = self.add_argument_group("section_freebayes")
        pipeline_group.add_argument("--freebayes-ploidy", default=1)

        pipeline_group = self.add_argument_group("section_spades")
        pipeline_group.add_argument("--spades-memory", default=64, help="max memory to be used in Gb")

        pipeline_group = self.add_argument_group("section_digital_normalisation")
        pipeline_group.add_argument(
            "--digital-normalisation-max-memory-usage",
            default=4e9,
            help="maximum amount of memory to use for data  normalisation",
        )

        self.add_argument("--run", default=False, action="store_true",
            help="execute the pipeline directly")

    def parse_args(self, *args):
        args_list = list(*args)
        if "--from-project" in args_list:
            if len(args_list) > 2:
                msg = (
                    "WARNING [sequana]: With --from-project option, "
                    + "pipeline and data-related options will be ignored."
                )
                print(col.error(msg))
            for action in self._actions:
                if action.required is True:
                    action.required = False
        options = super(Options, self).parse_args(*args)
        return options


def main(args=None):

    if args is None:
        args = sys.argv

    # whatever needs to be called by all pipeline before the options parsing
    before_pipeline(NAME)

    # option parsing including common epilog
    options = Options(NAME, epilog=sequana_epilog).parse_args(args[1:])

    # use profile slurm if user set a slurm queue
    if options.slurm_queue != "common":
        options.profile = "slurm"

    # the real stuff is here
    manager = SequanaManager(options, NAME)

    # create the beginning of the command and the working directory
    manager.setup()

    # fill the config file with input parameters
    if options.from_project is None:
        cfg = manager.config.config
        cfg.input_directory = os.path.abspath(options.input_directory)
        cfg.input_pattern = options.input_pattern
        cfg.input_readtag = options.input_readtag

        # ---------------------------------------------------- freebayes
        cfg.freebayes.ploidy = options.freebayes_ploidy

        # ----------------------------------------------------- quast
        if options.quast_reference:
            cfg.quast.reference = os.path.abspath(options.quast_reference)

        # ----------------------------------------------------- prokka
        if options.skip_prokka:
            cfg.prokka.do = False
        else:
            cfg.prokka.do = True
        cfg.prokka.kingdom = options.prokka_kingdom

        # ------------------------------------------------------ coverage
        if options.sequana_coverage_circular:
            cfg.sequana_coverage.circular = options.sequana_coverage_circular

        # ---------------------------------------------------------- spades
        cfg.spades.memory = options.spades_memory
        cfg.spades.resources.mem = f"{options.spades_memory}G"

        # -------------------------------------------- digital normalisation
        cfg.digital_normalisation.max_memory_usage = options.digital_normalisation_max_memory_usage

    # finalise the command and save it; copy the snakemake. update the config
    # file and save it.
    manager.teardown()

    if options.run:
        subprocess.Popen(["sh", '{}.sh'.format(NAME)], cwd=options.workdir)

if __name__ == "__main__":
    main()
