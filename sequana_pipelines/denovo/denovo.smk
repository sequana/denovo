#  This file is part of Sequana software
#
#  Copyright (c) 2016-2022 - Sequana Dev Team (https://sequana.readthedocs.io)
#
#  Distributed under the terms of the 3-clause BSD license.
#  The full license is in the LICENSE file, distributed with this software.
#
#  Website:       https://github.com/sequana/sequana
#  Website:       https://github.com/sequana/denovo
#  Documentation: http://sequana.readthedocs.io
#  Documentation: https://github.com/sequana/denovo/README.rst
##############################################################################
"""Short Read De Novo assembly pipeline"""
from sequana_pipetools.snaketools import PipelineManager


configfile: "config.yaml"


manager = PipelineManager("denovo", config, schema="schema.yaml")
sequana_wrapper_branch = "main"


rule denovo:
    input:
        "multiqc/multiqc_report.html",
        ".sequana/rulegraph.svg",


def requested_output(manager):
    """Resolve all needed output knowing the user config."""
    output_list = [
        expand("{sample}/quast/quast.done", sample=manager.samples),
        expand("{sample}/summary/{sample}.json", sample=manager.samples),
    ]
    if config["sequana_coverage"]["do"]:
        output_list += [
            expand(
                "{sample}/sequana_coverage/sequana_coverage.html",
                sample=manager.samples,
            )
        ]
    if config["prokka"]["do"]:
        output_list += [expand("{sample}/prokka/{sample}.gbk", sample=manager.samples)]
    if config["freebayes"]["do"]:
        output_list += [
            expand("{sample}/vcf_filter/{sample}.filter.vcf", sample=manager.samples)
        ]
    if config["busco"]["do"]:
        output_list += [expand("{sample}/busco/", sample=manager.samples)]
    if config["blast"]["do"]:
        output_list += [expand("{sample}/blast/{sample}.tsv", sample=manager.samples)]
    return output_list


# Function that define pipeline path
def get_raw_fastq(wildcards):
    """Get raw data"""
    return manager.samples[wildcards.sample]


def get_normalized_fastq(wildcards):
    """Get normalized data"""
    sample = wildcards.sample
    if config["digital_normalisation"]["do"]:
        if manager.paired:
            return [
                f"{sample}/digital_normalisation/{sample}_R{i}_.dn.fastq"
                for i in (1, 2)
            ]
        return [f"{sample}/digital_normalisation/{sample}_R1_.dn.fastq"]
    return get_raw_fastq(wildcards)


def get_assembly(wildcards):
    """Get assembly"""
    sample = wildcards.sample
    if config["assembler"] == "unicycler":
        return f"{sample}/unicycler/{sample}.fasta"
    return f"{sample}/spades/{sample}.scaffolds.fasta"


def get_markdup_bam(wildcards):
    """Get markdup bam file"""
    sample = wildcards.sample
    if config["sambamba_markdup"]["do"]:
        return f"{sample}/sambamba_markdup/{sample}.sorted.bam"
    return f"{sample}/bwa/{sample}.sorted.bam"


def get_filtered_bam(wildcards):
    """Get filtered bam file"""
    sample = wildcards.sample
    if config["sambamba_filter"]["do"]:
        return f"{sample}/sambamba_filter/{sample}.sorted.bam"
    return get_markdup_bam(wildcards)


def get_sequana_coverage_input(config):
    input_file = {
        "bed": "{sample}/samtools_depth/{sample}.bed",
        "fasta": "{sample}/seqkit_filter/{sample}.fasta",
    }
    if config["prokka"]["do"]:
        input_file["gbk"] = "{sample}/prokka/{sample}.gbk"
    return input_file


def create_prokka_option(config):
    """ create options with default prokka options.
    """
    kingdom = config.get("kingdom", "Bacteria")
    genus = config.get("genus", "genus")
    species = config.get("species", "species")
    return f"--kingdom {kingdom} --genus {genus} --species {species} {config['options']}"


def get_rulegraph_mapper(config):
    mapper = {"quast": "../quast/icarus.html"}
    if config["sequana_coverage"]["do"]:
        mapper.update({"sequana_coverage": "../sequana_coverage.html"})
    if config["freebayes"]["do"]:
        mapper.update({"freebayes_vcf_filter": "../variant_calling.html"})
    return mapper


# rules
rule digital_normalisation:
    input:
        fastq=get_raw_fastq,
    output:
        fastq=[
            f"{{sample}}/digital_normalisation/{{sample}}_R{i}_.dn.fastq"
            for i in range(1, 2 + manager.paired)
        ],
    log:
        "{sample}/logs/digital_normalisation.log",
    params:
        ksize=config["digital_normalisation"]["ksize"],
        cutoff=config["digital_normalisation"]["cutoff"],
        m=config["digital_normalisation"]["max_memory_usage"],
        options=config["digital_normalisation"]["options"]
    threads: config["digital_normalisation"]["threads"]
    container: config["apptainers"]["digital_normalisation"]
    resources:
        **config["digital_normalisation"]["resources"],
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/digital_normalisation"


rule spades:
    input:
        get_normalized_fastq,
    output:
        contigs="{sample}/spades/{sample}.contigs.fasta",
        scaffolds="{sample}/spades/{sample}.scaffolds.fasta",
    params:
        k=config["spades"]["k"],
        preset=config["spades"]["preset"],
        options=config["spades"]["options"],
        memory=config["spades"]["memory"],
    log:
        "{sample}/logs/spades.log",
    threads: config["spades"]["threads"]
    container: config["apptainers"]["spades"]
    resources:
        **config["spades"]["resources"],
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/spades"


rule unicycler:
    input:
        get_normalized_fastq,
    output:
        "{sample}/unicycler/{sample}.fasta"
    params:
        mode=config["unicycler"]["mode"],
        options=config["unicycler"]["options"],
    log:
        "{sample}/logs/unicycler.log",
    threads: config["unicycler"]["threads"]
    container: config["apptainers"]["unicycler"]
    resources:
        **config["unicycler"]["resources"],
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/unicycler"

rule quast:
    input:
        fastq=get_normalized_fastq,
        assembly=get_assembly,
    output:
        "{sample}/quast/quast.done",
    log:
        "{sample}/logs/quast.log",
    params:
        reference=config["quast"]["reference_file"],
        annotation=config["quast"]["annotation_file"],
        options=config["quast"]["options"],
    threads: config["quast"]["threads"]
    container: config["apptainers"]["quast"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/quast"


rule seqkit_filter:
    input:
        get_assembly,
    output:
        "{sample}/seqkit_filter/{sample}.fasta",
    log:
        "{sample}/logs/seqkit_filter.log",
    params:
        config["seqkit_filter"]["threshold"],
    container: config["apptainers"]["seqkit"]
    shell:
        """
        seqkit seq -i --id-regexp "^(.+)_cov.*" --min-len {params} {input} --out-file {output} > {log} 2>&1
        """


rule prokka:
    input:
        "{sample}/seqkit_filter/{sample}.fasta",
    output:
        "{sample}/prokka/{sample}.gbk",
    log:
        "{sample}/logs/prokka.log",
    params:
        options=create_prokka_option(config["prokka"])
    threads: config["prokka"]["threads"]
    container: config["apptainers"]["prokka"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/prokka"


rule busco:
    input:
        "{sample}/seqkit_filter/{sample}.fasta",
    output:
       directory("{sample}/busco"),
    log:
        "{sample}/logs/busco.log",
    params:
        mode="genome",
        lineage=config["busco"]["lineage"],
        short_summary_filename="short_summary_{sample}.txt",
        options=config["busco"]["options"],
    threads: config["busco"]["threads"]
    container: config["apptainers"]["busco"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/busco"


rule bwa_index:
    input:
        reference="{sample}/seqkit_filter/{sample}.fasta",
    output:
        "{sample}/seqkit_filter/{sample}.fasta.bwt",
        "{sample}/seqkit_filter/{sample}.fasta.fai",
    log:
        "{sample}/logs/bwa_index.log",
    params:
        index_algorithm=config["bwa"]["index_algorithm"],
    threads: 2
    container: config['apptainers']['bwa']
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/bwa/build"


rule bwa:
    input:
        fastq=get_raw_fastq,
        reference="{sample}/seqkit_filter/{sample}.fasta",
        bwt="{sample}/seqkit_filter/{sample}.fasta.bwt",
        fai="{sample}/seqkit_filter/{sample}.fasta.fai",
    output:
        sorted="{sample}/bwa/{sample}.sorted.bam",
    log:
        "{sample}/logs/bwa_mem.log",
    params:
        options=config["bwa"]["options"],
    threads: config["bwa"]["threads"]
    container: config['apptainers']["bwa"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/bwa/align"


rule sambamba_markdup:
    input:
        "{sample}/bwa/{sample}.sorted.bam",
    output:
        bam="{sample}/sambamba_markdup/{sample}.sorted.bam",
    log:
        "{sample}/logs/sambamba_markdup.log",
    params:
        remove_duplicates=config["sambamba_markdup"]["remove"],
    container: config['apptainers']["sambamba"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/sambamba_markdup"


rule sambamba_filter:
    input:
        get_markdup_bam,
    output:
        "{sample}/sambamba_filter/{sample}.sorted.bam",
    log:
        "{sample}/logs/sambamba_filter.log",
    params:
        threshold=config["sambamba_filter"]["threshold"],
    container: config['apptainers']["sambamba"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/sambamba_filter"


rule freebayes:
    input:
        bam=get_filtered_bam,
        ref="{sample}/seqkit_filter/{sample}.fasta",
    output:
        "{sample}/freebayes/{sample}.raw.vcf",
    log:
        "{sample}/logs/freebayes.log",
    params:
        ploidy=config["freebayes"]["ploidy"],
        options=config["freebayes"]["options"],
    container: config['apptainers']["freebayes"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/freebayes"


rule freebayes_vcf_filter:
    input:
        "{sample}/freebayes/{sample}.raw.vcf",
    output:
        vcf="{sample}/vcf_filter/{sample}.filter.vcf",
        csv="{sample}/vcf_filter/{sample}.filter.csv",
        html="{sample}/variant_calling.html",
    params:
        filter_dict=config["vcf_filter"],
    container: config['apptainers']["freebayes"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/freebayes_vcf_filter"


rule samtools_depth:
    input:
        "{sample}/sambamba_filter/{sample}.sorted.bam",
    output:
        "{sample}/samtools_depth/{sample}.bed",
    log:
        "{sample}/logs/samtools_depth.log",
    container: config['apptainers']['samtools']
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/samtools_depth"


rule sequana_coverage:
    input:
        **get_sequana_coverage_input(config),
    output:
        "{sample}/sequana_coverage/sequana_coverage.html",
    log:
        "{sample}/logs/sequana_coverage.log",
    params:
        circular=config["sequana_coverage"]["circular"],
        window_size=config["sequana_coverage"]["window_size"],
        chunksize=config["sequana_coverage"]["chunksize"],
        double_threshold=config["sequana_coverage"]["double_threshold"],
        gc_window_size=config["sequana_coverage"]["gc_window_size"],
        high_threshold=config["sequana_coverage"]["high_threshold"],
        low_threshold=config["sequana_coverage"]["low_threshold"],
        mixture_models=config["sequana_coverage"]["mixture_models"],
    resources: **config["sequana_coverage"]["resources"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/sequana_coverage"



rule seqkit_head:
    input:
        "{sample}/seqkit_filter/{sample}.fasta"
    output:
        "{sample}/subset_contigs/{sample}.subset.fasta"
    params:
        n_first = config["seqkit_head"]["n_first"]
    container: config['apptainers']["seqkit"]
    shell:
        """
        seqkit head -n {params.n_first} -o {output} {input}
        """


rule blast:
    input:
        query="{sample}/subset_contigs/{sample}.subset.fasta",
        blastdb=config["blast"]["blastdb"],
    output:
        "{sample}/blast/{sample}.tsv"
    params:
        blast_type="blastn",
        db_type="nt",
        evalue=config['blast']['evalue'],
        outfmt=config['blast']['outfmt'],
        options=config['blast']['options']
    threads:
        config['blast']['threads']
    resources:
        **config["blast"]["resources"],
    container: config["apptainers"]["blast"]
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/blast/blast"


rule rulegraph:
    input:
        workflow.snakefile,
    output:
        "rulegraph/rulegraph.dot",
    params:
        configname="config.yaml",
        mapper=get_rulegraph_mapper(config),
        required_local_files=["schema.yaml"],
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/rulegraph"


rule dot2svg:
    input:
        "rulegraph/rulegraph.dot"
    output:
        ".sequana/rulegraph.svg"
    container:
        config['apptainers']['graphviz']
    shell:
        """dot -Tsvg {input} -o {output}"""



# ======================================================================= summary
# create a json file that summarise information of your pipeline
# they must be complete in the onsuccess block
rule summary:
    input:
        outputs=get_assembly,
        html=[],
        rulegraph=".sequana/rulegraph.svg",
        snakefile=workflow.snakefile,
        config="config.yaml",
    output:
        json="{sample}/summary/{sample}.json",
    run:
        import json
        import os.path

        summary = {
            "tool": "sequana_summary",
            "inputs": [],
            "outputs": [],
            "html": [os.path.realpath(f) for f in input["html"]],
            "rulegraph": os.path.realpath(input["rulegraph"]),
            "requirements": "",
            "snakefile": os.path.realpath(input["snakefile"]),
            "config": os.path.realpath(input["config"]),
            "name": "variant_calling",
        }
        js = json.dumps(summary, indent=4, sort_keys=True)
        with open(output["json"], "w") as fp:
            fp.write(js)


# =============================================================== multiqc
rule multiqc:
    input:
        requested_output(manager),
    output:
        "multiqc/multiqc_report.html",
    params:
        options=config["multiqc"]["options"],
        input_directory=config["multiqc"]["input_directory"],
        modules=config["multiqc"]["modules"],
    log:
        "multiqc/multiqc.log",
    wrapper:
        f"{sequana_wrapper_branch}/wrappers/multiqc"


# these rules don't need to be submit on a node.
localrules:
    rulegraph,
    multiqc,


onsuccess:
    import os
    import shutil
    import json
    import pandas as pd

    from sequana.utils.datatables_js import DataTable
    from sequana.modules_report.summary import SummaryModule, SummaryModule2
    from sequana.utils import config as conf
    from sequana import logger

    logger.setLevel("INFO")

    # ================================== main HTML report
    # Must be created first because we share the conf and its sections
    manager.clean_multiqc("multiqc/multiqc_report.html")
    intro = """<h2>Overview</h2>
            This pipeline builds denovo assemblies on a set of samples. Individual reports are available
            as well as a <a href="multiqc/multiqc_report.html">multiqc report</a>."""

    intro += "<h2>Individual Reports</h2>"

    # add summary table
    df = pd.DataFrame({"name": sorted(manager.samples)})
    N50s = []
    Ncontigs = []
    for filename in sorted(manager.samples):
        data = open(f"{filename}/quast/report.txt", "r")
        for line in data.readlines():
            if (
                line.startswith(r"# contigs")
                and ">=" not in line
                and "Largest" not in line
            ):
                Ncontigs.append(line.split()[2].strip())
            elif line.startswith("N50"):
                N50s.append(line.split()[1].strip())

    df["N50"] = N50s
    df["Ncontig"] = Ncontigs
    df["links"] = [f"{x}/summary.html" for x in df["name"]]
    dt = DataTable(df, "stats")
    dt.datatable.datatable_options = {
        "pageLength": len(manager.samples),
        "dom": "Bfrtip",
        "buttons": ["copy", "csv"],
    }
    dt.datatable.set_links_to_column("links", "name")
    intro += dt.create_javascript_function() + dt.create_datatable()


    data = {
        "name": "denovo",
        "rulegraph": ".sequana/rulegraph.svg",
    }

    conf.output_dir = os.path.abspath(".")
    s = SummaryModule2(data, intro=intro, workflow=False)

    # create summary pipeline for each samples
    report_dir_format = "{sample}"
    for proj in manager.samples.keys():
        conf.output_dir = proj
        filename = os.sep.join([proj, "summary", "data.json"])

        # ad sub section for variant calling
        if manager.config.freebayes.do:
            conf.summary_sections.append(
                {
                    "name": "sequana coverage",
                    "anchor": "sequana_coverage",
                    "content": f'To get information about variants found in your sample, please visit the <a href="variant_calling.html">variant</a> page.',
                }
            )

        # Variant calling
        if manager.config.sequana_coverage.do:
            conf.summary_sections.append(
                {
                    "name": "sequana coverage",
                    "anchor": "sequana_coverage",
                    "content": f'The contigs are checked for coverage and reports are available in the <a href="sequana_coverage/sequana_coverage.html">coverage/</a> page.',
                }
            )

        # Prokka section
        if manager.config.prokka.do:
            conf.summary_sections.append(
                {
                    "name": "Prokka",
                    "anchor": "prokka",
                    "content": f'Prokka results can be found in <a href="prokka/">prokka/</a> directory where you can find GFF, genbank and other related file ready to use.',
                }
            )

        # quast
        conf.summary_sections.append(
            {
                "name": "Quast",
                "anchor": "quast",
                "content": f'The quality assessements can also be investigated using the quast <a href="quast/icarus.html"> reports </a>.',
            }
        )

        SummaryModule(json.loads(open(filename).read()))

    shell("chmod -R g+w .")
    manager.teardown()


onerror:
    from sequana_pipetools.errors import PipeError

    p = PipeError("denovo")
    p.status()
