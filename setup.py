from setuptools import find_packages, setup

setup(
    name="nmdc-server",
    version="0.1",
    packages=find_packages(),
    python_requires=">=3.6.0",
    install_requires=[
        # pinned because recent versions throw an error when upgrading through
        # the api at nmdc_server/jobs.py:34
        "alembic==1.5.8",
        "authlib",
        "celery[redis,librabbitmq]",
        "click",
        "cryptography<3.4",  # https://github.com/pyca/cryptography/issues/5771
        "fastapi==0.61.0",
        "factory-boy",
        "httpx",
        "itsdangerous",
        "psycopg2-binary",
        "pymongo",
        "python-dateutil",
        "python-dotenv",
        "requests",
        "sentry-sdk[celery,sqlalchemy]",
        "sqlalchemy>=1.3.18",
        "starlette==0.13.6",
        "typing-extensions",
    ],
    include_package_data=True,
    entry_points="""
        [console_scripts]
        nmdc-server = nmdc_server.cli:cli
    """,
)
