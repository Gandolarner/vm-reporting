from app.cli.commands import cli_app
from app.utils.logging_config import configure_logging

configure_logging()

if __name__== "__main__":
    cli_app()