import requests

"""
Deprecated REST-based vCenter client.

This client was used for the initial API proof of concept.
The main application now uses PyVmomiClient because performance metrics
are accessed through the vSphere Web Services API / PerformanceManager.
"""


class VCenterClient:
    """
    Simple vCenter REST API client.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

        self.session = requests.Session()

    def login(self) -> str:
        """
        Authenticate against the vCenter REST API
        and return the session token.
        """

        url = f"{self.base_url}/rest/com/vmware/cis/session"

        response = self.session.post(
            url,
            auth=(self.username, self.password),
            verify=self.verify_ssl,
        )

        response.raise_for_status()

        session_token = response.json()["value"]

        self.session.headers.update(
            {
                "vmware-api-session-id": session_token,
            }
        )

        return session_token

    def get_vms(self) -> list[dict]:
        """
        Return all virtual machines.
        """

        url = f"{self.base_url}/rest/vcenter/vm"

        response = self.session.get(
            url,
            verify=self.verify_ssl,
        )

        response.raise_for_status()

        return response.json()["value"]
    
    def get_vm_inventory(self) -> list[dict]:
        """
        Return normalized VM inventory data.
        """

        raw_vms = self.get_vms()

        inventory = []

        for vm in raw_vms:
            inventory.append(
                {
                    "moid": vm["vm"],
                    "name": vm["name"],
                    "power_state": vm["power_state"],
                    "cpu_count": vm["cpu_count"],
                    "memory_size_mib": vm["memory_size_MiB"],
                }
            )

        return inventory
    
    def get_vm_details(
        self,
        moid: str,
    ) -> dict:
        """
        Return detailed information for a VM.
        """

        url = f"{self.base_url}/rest/vcenter/vm/{moid}"

        response = self.session.get(
            url,
            verify=self.verify_ssl,
        )

        response.raise_for_status()

        return response.json()["value"]
    
    def get_raw(
        self,
        path: str,
    ) -> dict:
        """
        Execute a raw GET request against the vCenter API.
        """

        url = f"{self.base_url}{path}"

        response = self.session.get(
            url,
            verify=self.verify_ssl,
        )

        response.raise_for_status()

        return response.json()