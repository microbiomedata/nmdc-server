from setuptools import find_packages, setup

setup(
    name="nmdc-server",
    version="0.1",
    packages=find_packages(),
    python_requires=">=3.6.0",
    install_requires=[
        "alembic",
        "authlib",
        "fastapi==0.61.0",
        "factory-boy",
        "httpx",
        "itsdangerous",
        "psycopg2-binary",
        "python-dateutil",
        "python-dotenv",
        "sqlalchemy",
        "starlette==0.13.6",
        "typing-extensions",
    ],
)
