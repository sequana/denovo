import os
import subprocess
import tempfile

import pytest
from click.testing import CliRunner

from sequana_pipelines.denovo.main import main

from . import test_dir

input_dir = os.sep.join((test_dir, "data"))


def test_standalone_subprocess():
    directory = tempfile.TemporaryDirectory()
    cmd = ["sequana_denovo", "--input-directory", input_dir, "--working-directory", directory.name, "--force"]
    subprocess.call(cmd)


def test_standalone_script():
    directory = tempfile.TemporaryDirectory()
    runner = CliRunner()
    results = runner.invoke(
        main,
        ["--input-directory", input_dir, "--working-directory", directory.name, "--force"],
    )
    assert results.exit_code == 0


def test_standalone_script_skip_prokka():
    directory = tempfile.TemporaryDirectory()
    runner = CliRunner()
    results = runner.invoke(
        main,
        [
            "--input-directory", input_dir,
            "--working-directory", directory.name,
            "--force",
            "--skip-prokka",
        ],
    )
    assert results.exit_code == 0


def test_standalone_script_with_assembler_options():
    directory = tempfile.TemporaryDirectory()
    runner = CliRunner()
    results = runner.invoke(
        main,
        [
            "--input-directory", input_dir,
            "--working-directory", directory.name,
            "--force",
            "--spades-memory", "32",
            "--digital-normalisation-max-memory-usage", "1e9",
        ],
    )
    assert results.exit_code == 0


def test_version():
    cmd = ["sequana_denovo", "--version"]
    subprocess.call(cmd)
