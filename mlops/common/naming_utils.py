"""This module contains a few utility methods that allows us to generate names for \
    for experiments and runs."""

import subprocess
import os
import uuid


def generate_slot_name():
    """
    Generate a unique slot name based on the current branch to deploy azure functions.

    Returns:
        string: slot name according to the pattern
    """
    git_branch = os.environ.get("BUILD_SOURCEBRANCHNAME")

    if git_branch is None:
        git_branch = subprocess.check_output(
            "git rev-parse --abbrev-ref HEAD", shell=True, universal_newlines=True
        ).strip()

    git_branch = git_branch.split("/")[-1].replace("_", "-")
    return f"{git_branch}"


def generate_index_name():
    """
    Generate a unique index name based on the current branch name.

    Returns:
        string: index name according to the pattern
    """
    git_branch = os.environ.get("BUILD_SOURCEBRANCHNAME")

    if git_branch is None:
        git_branch = subprocess.check_output(
            "git rev-parse --abbrev-ref HEAD", shell=True, universal_newlines=True
        ).strip()

    git_branch = git_branch.split("/")[-1].replace("_", "-")
    return f"{git_branch}-index"


def generate_indexer_name():
    """
    Generate a unique indexer name based on the current branch name.

    Returns:
        string: indexer name according to the pattern
    """
    git_branch = os.environ.get("BUILD_SOURCEBRANCHNAME")

    if git_branch is None:
        git_branch = subprocess.check_output(
            "git rev-parse --abbrev-ref HEAD", shell=True, universal_newlines=True
        ).strip()

    git_branch = git_branch.split("/")[-1].replace("_", "-")
    return f"{git_branch}-indexer"


def generate_data_source_name():
    """
    Generate a unique data source connection name based on the current branch name.

    Returns:
        string: data source name according to the pattern
    """
    git_branch = os.environ.get("BUILD_SOURCEBRANCHNAME")

    if git_branch is None:
        git_branch = subprocess.check_output(
            "git rev-parse --abbrev-ref HEAD", shell=True, universal_newlines=True
        ).strip()

    git_branch = git_branch.split("/")[-1].replace("_", "-")
    return f"{git_branch}-data"


def generate_skillset_name():
    """
    Generate a unique skillset name based on the current branch name.

    Returns:
        string: skillset name according to the pattern
    """
    git_branch = os.environ.get("BUILD_SOURCEBRANCHNAME")

    if git_branch is None:
        git_branch = subprocess.check_output(
            "git rev-parse --abbrev-ref HEAD", shell=True, universal_newlines=True
        ).strip()

    git_branch = git_branch.split("/")[-1].replace("_", "-")
    return f"{git_branch}-skillset"


def generate_experiment_name(experiment_type: str):
    """
    Generate a unique experiment name based on the current branch name as well as an input parameter.

    Parameters:
     experiment_type (str): a prefix of the experiment name that usually contains the pipeline name \
        that helps to generate own experiment name for each pipeline in the repository.

    Returns:
        string: experiment name according to the pattern
    """
    git_branch = os.environ.get("BUILD_SOURCEBRANCHNAME")

    if git_branch is None:
        git_branch = subprocess.check_output(
            "git rev-parse --abbrev-ref HEAD", shell=True, universal_newlines=True
        ).strip()

    git_branch = git_branch.split("/")[-1]
    return f"{experiment_type}_{git_branch}"


def generate_run_name():
    """
    Generate a run name using build_id from the environment or autogenerated guid and run_ as a prefix.

    Returns:
        string: a unique run name
    """
    build = os.environ.get("BUILD_BUILDID")

    if build is None:
        build = f"local_{uuid.uuid4().hex}"

    return f"run_{build}"
