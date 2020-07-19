import sys
import os
import argparse

from sequana_pipetools.options import *
from sequana_pipetools.misc import Colors
from sequana_pipetools.info import sequana_epilog, sequana_prolog

col = Colors()

NAME = "denovo"


class Options(argparse.ArgumentParser):
    def __init__(self, prog=NAME, epilog=None):
        usage = col.purple(sequana_prolog.format(**{"name": NAME}))
        super(Options, self).__init__(usage=usage, prog=prog, description="",
            epilog=epilog,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        # add a new group of options to the parser
        so = SlurmOptions()
        so.add_options(self)

        # add a snakemake group of options to the parser
        so = SnakemakeOptions(working_directory=NAME)
        so.add_options(self)

        so = InputOptions()
        so.add_options(self)

        so = GeneralOptions()
        so.add_options(self)

        pipeline_group = self.add_argument_group("pipeline")
        pipeline_group.add_argument("--quast-reference", default=None, type=str)

        pipeline_group = self.add_argument_group("section_prokka")
        pipeline_group.add_argument("--skip-prokka", action="store_true")
        pipeline_group.add_argument("--prokka-kingdom", default="Bacteria",
            type=str, choices=["Archaea", "Mitochondria", "Viruses", "Bacteria"])

        pipeline_group = self.add_argument_group("section_sequana_coverage")
        pipeline_group.add_argument("--sequana-coverage-circular", action="store_true")

        pipeline_group = self.add_argument_group("section_freebayes")
        pipeline_group.add_argument("--freebayes-ploidy", default=1)

        pipeline_group = self.add_argument_group("section_spades")
        pipeline_group.add_argument("--spades-memory", default=64, 
            help="max memory to be used in Gb")

        pipeline_group = self.add_argument_group("section_digital_normalisation")
        pipeline_group.add_argument("--digital-normalisation-max-memory-usage", 
            default=4e9, 
            help="maximum amount of memory to use for data  normalisation")

    def parse_args(self, *args):
        args_list = list(*args)
        if "--from-project" in args_list:
            if len(args_list)>2:
                msg = "WARNING [sequana]: With --from-project option, " + \
                        "pipeline and data-related options will be ignored."
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
    from sequana_pipetools.options import before_pipeline
    before_pipeline(NAME)

    # option parsing including common epilog
    options = Options(NAME, epilog=sequana_epilog).parse_args(args[1:])


    from sequana.pipelines_common import SequanaManager

    # the real stuff is here
    manager = SequanaManager(options, NAME)

    # create the beginning of the command and the working directory
    manager.setup()

    # fill the config file with input parameters
    if options.from_project is None:
        cfg = manager.config.config
        # EXAMPLE TOREPLACE WITH YOUR NEEDS
        cfg.input_directory = os.path.abspath(options.input_directory)
        cfg.input_pattern = options.input_pattern
        cfg.input_readtag = options.input_readtag

        #manager.exists(cfg.general.reference_file)

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

        # -------------------------------------------- digital normalisation
        cfg.digital_normalisation.max_memory_usage = options.digital_normalisation_max_memory_usage

    # finalise the command and save it; copy the snakemake. update the config
    # file and save it.
    manager.teardown()


if __name__ == "__main__":
    main()
