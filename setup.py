from setuptools import find_packages, setup

setup(
    name="nmdc-server",
    version="0.1",
    packages=find_packages(),
    python_requires=">=3.6.0",
    install_requires=["fastapi"],
)
