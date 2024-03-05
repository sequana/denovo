import os
import subprocess
import sys
import tempfile

import easydev
from click.testing import CliRunner

from sequana_pipelines.denovo.main import main

from . import test_dir

sharedir = test_dir + "/data"


def test_standalone_subprocess(tmpdir):
    cmd = f"""sequana_denovo --input-directory {sharedir}
          --working-directory {tmpdir} --force"""
    subprocess.call(cmd.split())


def test_standalone_script():
    directory = tempfile.TemporaryDirectory()

    runner = CliRunner()
    results = runner.invoke(main, ["--input-directory", sharedir, "--working-directory", directory.name, "--force"])
    assert results.exit_code == 0


def test_full(tmpdir):

    wk = tmpdir

    cmd = "sequana_denovo --input-directory {} "
    cmd += "--working-directory {}  --force "
    cmd += " --digital-normalisation-max-memory-usage 1e9"
    cmd += " --skip-prokka"
    cmd = cmd.format(sharedir, wk)
    subprocess.call(cmd.split())

    stat = subprocess.call("sh denovo.sh".split(), cwd=wk)

    assert os.path.exists(wk + "/summary.html")


def test_version():
    cmd = "sequana_denovo --version"
    subprocess.call(cmd.split())
