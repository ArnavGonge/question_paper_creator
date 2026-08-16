import tomllib
from pathlib import Path


def test_streamlit_cloud_installs_src_package():
    requirements = Path("requirements.txt").read_text().splitlines()
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    editable_index = requirements.index("-e .")
    setuptools_index = next(
        index
        for index, requirement in enumerate(requirements)
        if requirement.startswith("setuptools==")
    )
    assert setuptools_index < editable_index
    assert "-e ." in requirements
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
