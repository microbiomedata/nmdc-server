from setuptools import find_packages, setup

setup(
    name="nmdc-server",
    version="0.1",
    packages=find_packages(),
    python_requires=">=3.9.0",
    install_requires=[
        # pinned because recent versions throw an error when upgrading through
        # the api at nmdc_server/jobs.py:34
        "alembic==1.5.8",
        "authlib==0.15.5",
        "celery[redis]",
        "click",
        "cryptography<3.4",  # https://github.com/pyca/cryptography/issues/5771
        "dnspython==2.3.0",  # https://github.com/microbiomedata/nmdc-server/actions/runs/5671884086/job/15369921721
        "fastapi==0.71.0",
        "factory-boy==3.2.1",
        "httpx<=0.18.2",
        "ipython==7.31.1",
        "itsdangerous==2.0.1",
        "mypy<0.920",
        "nmdc-schema==7.7.0",
        "pint==0.18",
        "psycopg2==2.9.3",
        "pydantic==1.8.2",
        "pymongo>=4.0.0",
        "python-dateutil",
        "python-dotenv",
        "requests==2.28.1",
        "sentry-sdk[celery,sqlalchemy]",
        "sqlalchemy>=1.4",
        "starlette==0.17.1",
        "typing-extensions==4.0.1",
        # pinned 3rd party dependencies
        "importlib-metadata==4.12.0",
    ],
    include_package_data=True,
    entry_points="""
        [console_scripts]
        nmdc-server = nmdc_server.cli:cli
    """,
)
