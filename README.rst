
.. image:: https://badge.fury.io/py/sequana-denovo.svg
     :target: https://pypi.python.org/pypi/sequana_denovo

.. image:: https://github.com/sequana/denovo/actions/workflows/main.yml/badge.svg
   :target: https://github.com/sequana/denovo/actions/workflows/main.yml

.. image:: https://coveralls.io/repos/github/sequana/denovo/badge.svg?branch=main
    :target: https://coveralls.io/github/sequana/denovo?branch=main

.. image:: https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C3.10-blue.svg
    :target: https://pypi.python.org/pypi/sequana
    :alt: Python 3.8 | 3.9 | 3.10

.. image:: http://joss.theoj.org/papers/10.21105/joss.00352/status.svg
   :target: http://joss.theoj.org/papers/10.21105/joss.00352
   :alt: JOSS (journal of open source software) DOI

This is is the **denovo** pipeline from the `Sequana <https://sequana.readthedocs.org>`_ projet


:Overview: a de-novo assembly pipeline for short-read sequencing data
:Input: A set of FastQ files
:Output: Fasta, VCF, HTML report
:Status: production
:Citation: Cokelaer et al, (2017), ‘Sequana’: a Set of Snakemake NGS pipelines, Journal of Open Source Software, 2(16), 352, JOSS DOI doi:10.21105/joss.00352


Installation
~~~~~~~~~~~~

**sequana_denovo** is based on Python3, just install the package as follows::

    pip install sequana --upgrade

You will need third-party software such as fastqc. Please see below for details.

Usage
~~~~~

The following command will scan all files ending in .fastq.gz found in the local
directory, create a directory called denovo/ where a snakemake pipeline is
stored. Depending on the number of files and their sizes, the
process may be long::

::

    sequana_denovo --help
    sequana_denovo --input-directory DATAPATH 

This creates a directory with the pipeline and configuration file. You will then need 
to execute the pipeline::

    cd denovo
    sh denovo.sh  # for a local run

This launch a snakemake pipeline. If you are familiar with snakemake, you can 
retrieve the pipeline itself and its configuration files and then execute the pipeline yourself with specific parameters::

    snakemake -s denovo.smk -c config.yaml --cores 4 --stats stats.txt

Or use `sequanix <https://sequana.readthedocs.io/en/main/sequanix.html>`_ interface.

Requirements
~~~~~~~~~~~~

This pipelines requires the following executable(s):

- spades
- busco
- bwa
- khmer : there is not executable called kmher but a set of executables (.e.g .normalize-by-median.py)
- freebayes
- picard
- prokka
- quast
- spades
- sambamba
- samtools



.. image:: https://raw.githubusercontent.com/sequana/sequana_denovo/main/sequana_pipelines/denovo/dag.png


Details
~~~~~~~~~


Snakemake *de-novo* assembly pipeline dedicates to small genome like bacteria.
It is based on `SPAdes <http://cab.spbu.ru/software/spades/>`_.
The assembler corrects reads and then assemble them using different size of kmer.
If the correct option is set, SPAdes corrects mismatches and short INDELs in
the contigs using BWA.

The sequencing depth can be normalised with `khmer <https://github.com/dib-lab/khmer>`_.
Digital normalisation converts the existing high coverage regions into a Gaussian
distributions centered around a lower sequencing depth. To put it another way,
genome regions covered at 200x will be covered at 20x after normalisation. Thus,
some reads from high coverage regions are discarded to reduce the quantity of data.
Although the coverage is drastically reduce, the assembly will be as good or better
than assembling the unnormalised data. Furthermore, SPAdes with normalised data
is notably speeder and cost less memory than without digital normalisation.
Above all, khmer does this in fixed, low memory and without any reference
sequence needed.

The pipeline assess the assembly with several tools and approach. The first one
is `Quast <http://quast.sourceforge.net/>`_, a tools for genome assemblies
evaluation and comparison. It provides a HTML report with useful metrics like
N50, number of mismatch and so on. Furthermore, it creates a viewer of contigs
called `Icarus <http://quast.sourceforge.net/icarus.html>`_.

The second approach is to characterise coverage with sequana coverage and
to detect mismatchs and short INDELs with
`Freebayes <https://github.com/ekg/freebayes>`_.

The last approach but not the least is `BUSCO <http://busco.ezlab.org/>`_, that
provides quantitative measures for the assessment of genome assembly based on
expectations of gene content from near-universal single-copy orthologs selected
from `OrthoDB <http://www.orthodb.org/>`_.


========= ====================================================================
Version   Description
========= ====================================================================
0.10.0    * use click / include multiqc apptainer
0.9.0     * Major refactoring to include apptainers, use wrappers
0.8.5     * add multiqc and use newest version of sequana
0.8.4     * update pipeline to use new pipetools features
0.8.3     * fix requirements (spades -> spades.py)
0.8.2     * fix readtag, update config to account for new coverage setup
0.8.1 
0.8.0     **First release.**
========= ====================================================================
