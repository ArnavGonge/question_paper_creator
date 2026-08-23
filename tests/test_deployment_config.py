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


def test_streamlit_runtime_uses_light_neutral_theme():
    config = tomllib.loads(Path(".streamlit/config.toml").read_text())

    assert config["theme"] == {
        "base": "light",
        "primaryColor": "#0F766E",
        "backgroundColor": "#F5F7F8",
        "secondaryBackgroundColor": "#FFFFFF",
        "textColor": "#17202A",
        "linkColor": "#0F766E",
        "borderColor": "#D9E0E4",
        "showWidgetBorder": True,
        "showSidebarBorder": True,
        "baseRadius": "small",
        "buttonRadius": "small",
    }
