from importlib import resources


def load_template(resource_path: str) -> str:
    r"""
    Returns the contents of a template file as a string.

    Note: We do this via `importlib.resources` instead of a regular `open()` so
          that the path is accurate both when this script is run in a development
          environment and when this script is run when installed from PyPI,
          instead of it only being accurate in the former case.
          Reference: https://docs.python.org/3.9/library/importlib.html#importlib.resources.files

    Note: This function was copied from the `refscan` repository, at:
          https://github.com/microbiomedata/refscan/blob/a30ece13/refscan/grapher.py#L31-L42
    """

    package_name = "nmdc_server.swagger_ui.templates"
    return resources.files(package_name).joinpath(resource_path).read_text(encoding="utf-8")
