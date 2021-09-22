import easydev
import os
import tempfile
import subprocess
import sys

from . import test_dir

sharedir = test_dir + "/data"

def test_standalone_subprocess():
    directory = tempfile.TemporaryDirectory()
    cmd = """sequana_denovo --input-directory {}
          --working-directory --force""".format(sharedir, directory.name)
    subprocess.call(cmd.split())


def test_standalone_script():
    directory = tempfile.TemporaryDirectory()
    import sequana_pipelines.denovo.main as m
    sys.argv = ["test", "--input-directory", sharedir, "--working-directory",
        directory.name, "--force"]
    m.main()

def _test_full():

    with tempfile.TemporaryDirectory() as directory:
        print(directory)
        wk = directory

        cmd = "sequana_denovo --input-directory {} "
        cmd += "--working-directory {}  --force "
        cmd +=" --digital-normalisation-max-memory-usage 1e9"
        cmd +=" --skip-prokka"
        cmd = cmd.format(sharedir, wk)
        subprocess.call(cmd.split())

        stat = subprocess.call("sh denovo.sh".split(), cwd=wk)

        assert os.path.exists(wk + "/report_data/summary.html")

def test_version():
    cmd = "sequana_denovo --version"
    subprocess.call(cmd.split())

