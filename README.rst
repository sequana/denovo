
.. image:: https://badge.fury.io/py/sequana-denovo.svg
     :target: https://pypi.python.org/pypi/sequana_denovo

.. image:: https://github.com/sequana/denovo/actions/workflows/main.yml/badge.svg
   :target: https://github.com/sequana/denovo/actions/workflows/main.yml

.. image:: https://coveralls.io/repos/github/sequana/denovo/badge.svg?branch=main
    :target: https://coveralls.io/github/sequana/denovo?branch=main

.. image:: https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg
    :target: https://pypi.python.org/pypi/sequana
    :alt: Python 3.10 | 3.11 | 3.12

.. image:: http://joss.theoj.org/papers/10.21105/joss.00352/status.svg
   :target: http://joss.theoj.org/papers/10.21105/joss.00352
   :alt: JOSS (journal of open source software) DOI

This is the **denovo** pipeline from the `Sequana <https://sequana.readthedocs.org>`_ project.

:Overview: De-novo assembly pipeline for short-read Illumina data (bacterial genomes)
:Input: A set of paired or single-end FastQ files
:Output: Assembled FASTA contigs, annotation (GFF/GenBank), variant calls (VCF), HTML reports
:Status: Production
:Documentation: This README and https://sequana.readthedocs.io
:Citation: Cokelaer et al, (2017), 'Sequana': a Set of Snakemake NGS pipelines, Journal of Open Source Software, 2(16), 352, https://doi.org/10.21105/joss.00352


Installation
~~~~~~~~~~~~

If you already have all requirements, install the package with pip::

    pip install sequana_denovo --upgrade

You will need third-party tools (spades, prokka, quast, etc.). Install all dependencies at once::

    mamba env create -f environment.yml


Usage
~~~~~

Scan FastQ files in a directory and set up the pipeline (replace ``DATAPATH`` with your input directory)::

    sequana_denovo --input-directory DATAPATH

To skip Prokka annotation::

    sequana_denovo --input-directory DATAPATH --skip-prokka

To tune SPAdes memory (default 64 Gb) and digital normalisation::

    sequana_denovo --input-directory DATAPATH --spades-memory 32 --digital-normalisation-max-memory-usage 1e9

This creates a ``denovo/`` directory with the pipeline and configuration file. Execute the pipeline locally::

    cd denovo
    sh denovo.sh

If you are familiar with Snakemake, you can also run the pipeline directly::

    snakemake -s denovo.rules --cores 4 --stats stats.txt

See ``.sequana/profile/config.yaml`` to tune Snakemake behaviour (cores, cluster settings, etc.).


Usage with apptainer
~~~~~~~~~~~~~~~~~~~~~

With apptainer, initiate the working directory as follows::

    sequana_denovo --input-directory DATAPATH --use-apptainer

Images are downloaded in the working directory. To store them in a shared location::

    sequana_denovo --input-directory DATAPATH --use-apptainer --apptainer-prefix ~/.sequana/apptainers

Then run as usual::

    cd denovo
    sh denovo.sh


Requirements
~~~~~~~~~~~~

This pipeline requires the following executables (install via bioconda/conda):

- **spades** or **unicycler** — de-novo assembler (``--assembler`` option)
- **khmer** — digital normalisation (normalize-by-median.py, filter-abund.py, etc.)
- **quast** — assembly quality assessment
- **prokka** — genome annotation (optional, ``--skip-prokka``)
- **busco** — assembly completeness assessment (optional)
- **checkm-genome** — genome completeness and contamination (optional)
- **bwa** + **sambamba** — read mapping back to assembly
- **freebayes** — variant calling
- **samtools** — BAM/SAM processing
- **seqkit** — contig filtering by length
- **blast** — taxonomic identification of contigs (optional)
- **multiqc** — aggregated HTML report
- **graphviz** — pipeline DAG image


.. image:: https://raw.githubusercontent.com/sequana/denovo/main/sequana_pipelines/denovo/dag.svg


Details
~~~~~~~~~

This Snakemake pipeline assembles bacterial (or other small) genomes from short Illumina reads.

**Digital normalisation** (khmer): optionally reduces sequencing depth to a target coverage
level, discarding redundant reads. This lowers memory usage and speeds up assembly without
significantly impacting quality.

**Assembly**: SPAdes (default) or Unicycler. SPAdes uses multiple k-mer sizes and is
recommended for most bacterial genomes. Unicycler is designed for hybrid or circular assemblies.

**Quality assessment** (QUAST): reports assembly statistics (N50, # contigs, total length, GC%,
coverage depth) with an interactive Icarus contig browser.

**Annotation** (Prokka): rapid prokaryotic genome annotation producing GFF, GenBank, and
other standard formats.

**Coverage analysis** (sequana_coverage): reads are mapped back to the assembly with BWA,
duplicates flagged with Sambamba, and per-contig coverage profiles computed and visualised.

**Variant calling** (Freebayes): detects SNPs and small indels between the assembled
consensus and the mapped reads.

**Completeness** (BUSCO / CheckM): optionally assess assembly completeness against
conserved single-copy orthologs (BUSCO) or lineage-specific marker genes (CheckM).

**Taxonomic identification** (BLAST): optionally BLASTs the top contigs against the nt
database to identify their taxonomy.

A summary HTML report (``summary.html``) with per-sample assembly statistics and embedded
coverage plots is generated at the end of the run, alongside a MultiQC report.


Rules and configuration details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the `latest documented configuration file <https://raw.githubusercontent.com/sequana/denovo/main/sequana_pipelines/denovo/config.yaml>`_
for all available parameters.


Changelog
~~~~~~~~~

========= ====================================================================
Version   Description
========= ====================================================================
0.12.0    * Drop Python 3.8/3.9; require Python >=3.10
          * Drop click-completion dependency
          * Replace pkg_resources with importlib.metadata in __init__.py
          * Add exclude_pattern to config and schema
          * Fix digital_normalisation: use khmer:2.1.1 container from damona
            (zenodo record 13924243) instead of generic sequana_tools image
          * Fix digital_normalisation rule: convert run: to shell: for
            apptainer compatibility (container: + run: disallowed)
          * Fix spades, prokka, unicycler rules: add named input.fastq /
            input.assembly for wrapper compatibility
          * Fix bwa_index: add options param; bwa: drop tmp_directory,
            add options/resources params; new bwa/align v2 shell that
            separates bwa mem and sambamba sort into distinct steps
          * Fix sambamba_markdup/sambamba_filter: add missing params/resources
          * Fix samtools_depth: add named input.bam and options param
          * Fix prokka output: .gff instead of .gbk (matches wrapper)
          * Improved HTML report: per-sample summary.html with quast stats
            table and embedded coverage plots; main table links to per-sample
            reports; workflow=False on individual reports
          * Update environment.yml: add khmer, python>=3.10
          * Update tools.txt: add khmer scripts, graphviz
0.11.1    * Fix missing resources for quast/prokka/bwa_index
0.11.0    * add checkm
0.10.0    * use click / include multiqc apptainer
0.9.0     * Major refactoring to include apptainers, use wrappers
0.8.5     * add multiqc and use newest version of sequana
0.8.4     * update pipeline to use new pipetools features
0.8.3     * fix requirements (spades -> spades.py)
0.8.2     * fix readtag, update config to account for new coverage setup
0.8.1
0.8.0     **First release.**
========= ====================================================================


Contribute & Code of Conduct
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To contribute to this project, please take a look at the
`Contributing Guidelines <https://github.com/sequana/sequana/blob/main/CONTRIBUTING.rst>`_ first. Please note that this project is released with a
`Code of Conduct <https://github.com/sequana/sequana/blob/main/CONDUCT.md>`_. By contributing to this project, you agree to abide by its terms.
