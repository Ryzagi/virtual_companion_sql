from pathlib import Path

from setuptools import find_packages, setup

THIS_DIR = Path(__file__).parent


def _load_requirements(path_dir: Path):
    requirements_directory = path_dir / "requirements.txt"
    requirements = []
    with requirements_directory.open("r") as file:
        for line in file.readlines():
            requirements.append(line.lstrip())
    return requirements


setup(
    name="converbot",
    version="0.0.1",
    packages=find_packages(exclude=["tests", "config"]),
    install_requires=_load_requirements(THIS_DIR),
    entry_points={
        "console_scripts": [
            "run_converbot = converbot.app.run:main",
        ],
    },
)
