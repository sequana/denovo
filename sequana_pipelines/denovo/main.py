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
import os
import sys

import click_completion
import rich_click as click

click_completion.init()

NAME = "denovo"

from sequana_pipetools import SequanaManager
from sequana_pipetools.options import *

help = init_click(
    NAME,
    groups={
        "Pipeline Specific": [
            "--skip-prokka",
            "--prokka-kingdom",
            "--quast-reference",
            "--sequana-coverage-circular",
            "--freebayes-ploidy",
            "--spades-memory",
            "--digital-normalisation-max-memory-usage",
        ],
        "Pipeline Specific Completeness": ["--checkm-rank", "--checkm-name", "--busco-lineage"],
    },
)


@click.command(context_settings=help)
@include_options_from(ClickSnakemakeOptions, working_directory=NAME)
@include_options_from(ClickSlurmOptions)
@include_options_from(ClickInputOptions)
@include_options_from(ClickGeneralOptions)
@click.option("--quast-reference", default=None, type=click.STRING)
@click.option("--skip-prokka", is_flag=True)
@click.option(
    "--prokka-kingdom", default="Bacteria", type=click.Choice(["Archaea", "Mitochondria", "Viruses", "Bacteria"])
)
@click.option("--sequana-coverage-circular", is_flag=True)
@click.option("--freebayes-ploidy", default=1, type=click.INT)
@click.option("--spades-memory", default=64, type=click.INT, help="max memory to be used in Gb")
@click.option(
    "--digital-normalisation-max-memory-usage",
    default=4e9,
    help="maximum amount of memory to use for data  normalisation",
)
@click.option(
    "--busco-lineage",
    "lineage",
    help="Lineage or path to lineage file for BUSCO. Note that we support only version 5 of the BUSCO lineage.",
)
@click.option(
    "--checkm-rank",
    default="genus",
    show_default=True,
    help="For bacteria, checkm can be used. Usually at the genus level. can be set to 'domain', 'phylum', 'class', 'order', 'family', 'genus', 'species'. ",
)
@click.option(
    "--checkm-name",
    default=None,
    help="checkm taxon name. Type checkm taxon_list for a complete list. You can also check the LORA wiki page here: https://github.com/sequana/lora/wiki/checkm",
)
def main(**options):
    # the real stuff is here
    manager = SequanaManager(options, NAME)
    options = manager.options

    # creates the working directory
    manager.setup()

    # fill the config file with input parameters
    # if options.from_project is None:
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

    # checkm
    if options.checkm_name and options.checkm_rank:
        cfg.checkm["do"] = True
        cfg.checkm["taxon_rank"] = options.checkm_rank
        cfg.checkm["taxon_name"] = options.checkm_name

    if options.lineage:
        cfg.busco["lineage"] = options.lineage

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


if __name__ == "__main__":
    main()
