import sys
import os
import argparse

from sequana.pipelines_common import *
from sequana.snaketools import Module
from sequana import logger
logger.level = "INFO"

col = Colors()

NAME = "denovo"
m = Module(NAME)
m.is_executable()


class Options(argparse.ArgumentParser):
    def __init__(self, prog=NAME):
        usage = col.purple(
            """This script prepares the sequana pipeline denovo layout to
            include the Snakemake pipeline and its configuration file ready to
            use.

            In practice, it copies the config file and the pipeline into a
            directory (denovo) together with an executable script

            For a local run, use :

                sequana_pipelines_denovo --input-directory PATH_TO_DATA 

            For a run on a SLURM cluster:

                sequana_pipelines_denovo --input-directory PATH_TO_DATA 

        """
        )
        super(Options, self).__init__(usage=usage, prog=prog, description="",
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


def main(args=None):

    if args is None:
        args = sys.argv

    options = Options(NAME).parse_args(args[1:])

    manager = PipelineManager(options, NAME)

    # create the beginning of the command and the working directory
    manager.setup()

    # fill the config file with input parameters
    cfg = manager.config.config
    # EXAMPLE TOREPLACE WITH YOUR NEEDS
    cfg.input_directory = os.path.abspath(options.input_directory)
    cfg.input_pattern = options.input_pattern

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
