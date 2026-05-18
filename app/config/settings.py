from dotenv import load_dotenv
import os


APP_ENV = os.getenv(
    "APP_ENV",
    "default",
)

if APP_ENV == "demo":
    load_dotenv(".env.demo")
else:
    load_dotenv(".env")


class Settings:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///data/vm_reporting.db",
    )

    VCENTER_HOST = os.getenv("VCENTER_HOST")
    VCENTER_USERNAME = os.getenv("VCENTER_USERNAME")
    VCENTER_PASSWORD = os.getenv("VCENTER_PASSWORD")

    VCENTER_PORT = int(
        os.getenv("VCENTER_PORT", 443)
    )

    VCENTER_VERIFY_SSL = (
        os.getenv("VCENTER_VERIFY_SSL", "false").lower()
        == "true"
    )

    REPORT_OUTPUT_DIR = os.getenv(
        "REPORT_OUTPUT_DIR",
        "output/reports",
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )


settings = Settings()