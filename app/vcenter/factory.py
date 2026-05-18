from app.config.settings import settings
from app.vcenter.pyvmomi_client import PyVmomiClient


def create_vcenter_client() -> PyVmomiClient:
    """
    Create a configured pyVmomi vCenter client.
    """

    if settings.VCENTER_HOST is None:
        raise ValueError(
            "VCENTER_HOST is not configured."
        )

    if settings.VCENTER_USERNAME is None:
        raise ValueError(
            "VCENTER_USERNAME is not configured."
        )

    if settings.VCENTER_PASSWORD is None:
        raise ValueError(
            "VCENTER_PASSWORD is not configured."
        )

    return PyVmomiClient(
        host=settings.VCENTER_HOST,
        username=settings.VCENTER_USERNAME,
        password=settings.VCENTER_PASSWORD,
        port=settings.VCENTER_PORT,
        verify_ssl=settings.VCENTER_VERIFY_SSL,
    )