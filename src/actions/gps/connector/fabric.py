import logging

import requests
from pydantic import Field

from actions.base import ActionConfig, ActionConnector
from actions.gps.interface import GPSAction, GPSInput
from providers.io_provider import IOProvider


class GPSFabricConfig(ActionConfig):
    """
    Configuration for GPS Fabric connector.

    Parameters
    ----------
    fabric_endpoint : str
        The endpoint URL for the Fabric network.
    request_timeout : int
        Timeout in seconds for HTTP requests.
    """

    fabric_endpoint: str = Field(
        default="http://localhost:8545",
        description="The endpoint URL for the Fabric network.",
    )
    request_timeout: int = Field(
        default=10,
        description="Timeout in seconds for HTTP requests.",
    )


class GPSFabricConnector(ActionConnector[GPSFabricConfig, GPSInput]):
    """
    Connector that shares GPS coordinates via a Fabric network.
    """

    def __init__(self, config: GPSFabricConfig):
        """
        Initialize the GPSFabricConnector.

        Parameters
        ----------
        config : GPSFabricConfig
            Configuration for the action connector.
        """
        super().__init__(config)

        # Set IO Provider
        self.io_provider = IOProvider()

        # Set fabric endpoint configuration
        self.fabric_endpoint = self.config.fabric_endpoint
        self.request_timeout = self.config.request_timeout

    async def connect(self, output_interface: GPSInput) -> None:
        """
        Connect to the Fabric network and send GPS coordinates.

        Parameters
        ----------
        output_interface : GPSInput
            The GPS input containing the action to be performed.
        """
        logging.info(f"GPSFabricConnector: {output_interface.action}")

        if output_interface.action == GPSAction.SHARE_LOCATION:
            # Send GPS coordinates to the Fabric network
            self.send_coordinates()

    def send_coordinates(self) -> bool:
        """
        Send GPS coordinates to the Fabric network.

        Returns
        -------
        bool
            True if coordinates were sent successfully, False otherwise.
        """
        logging.info("GPSFabricConnector: Sending coordinates to Fabric network.")
        
        # Retrieve coordinates from IO provider
        latitude = self.io_provider.get_dynamic_variable("latitude")
        longitude = self.io_provider.get_dynamic_variable("longitude")
        yaw = self.io_provider.get_dynamic_variable("yaw_deg")
        
        logging.info(f"GPSFabricConnector: Latitude: {latitude}")
        logging.info(f"GPSFabricConnector: Longitude: {longitude}")
        logging.info(f"GPSFabricConnector: Yaw: {yaw}")

        # Validate that all required coordinates are available
        # Fixed: Use 'or' instead of 'and' to catch partial coordinates
        if latitude is None or longitude is None or yaw is None:
            logging.error(
                f"GPSFabricConnector: Missing coordinates - "
                f"latitude: {latitude}, longitude: {longitude}, yaw: {yaw}"
            )
            return False

        try:
            # Send coordinates via JSON-RPC request
            share_status_response = requests.post(
                f"{self.fabric_endpoint}",
                json={
                    "method": "omp2p_shareStatus",
                    "params": [
                        {"latitude": latitude, "longitude": longitude, "yaw": yaw}
                    ],
                    "id": 1,
                    "jsonrpc": "2.0",
                },
                headers={"Content-Type": "application/json"},
                timeout=self.request_timeout,
            )
            
            # Validate HTTP status code
            share_status_response.raise_for_status()
            
            # Parse JSON response
            try:
                response = share_status_response.json()
            except requests.exceptions.JSONDecodeError as e:
                logging.error(
                    f"GPSFabricConnector: Invalid JSON response: {e}. "
                    f"Response text: {share_status_response.text[:200]}"
                )
                return False
            
            # Check for JSON-RPC error field
            if "error" in response:
                logging.error(
                    f"GPSFabricConnector: JSON-RPC error: {response['error']}"
                )
                return False
            
            # Check for successful result
            if "result" in response and response["result"]:
                logging.info("GPSFabricConnector: Coordinates shared successfully.")
                return True
            else:
                logging.error(
                    f"GPSFabricConnector: Failed to share coordinates. Response: {response}"
                )
                return False
                
        except requests.exceptions.Timeout:
            logging.error(
                f"GPSFabricConnector: Request timeout after {self.request_timeout}s"
            )
            return False
        except requests.exceptions.ConnectionError as e:
            logging.error(
                f"GPSFabricConnector: Connection error to {self.fabric_endpoint}: {e}"
            )
            return False
        except requests.exceptions.HTTPError as e:
            logging.error(
                f"GPSFabricConnector: HTTP error {e.response.status_code}: {e}"
            )
            return False
        except requests.RequestException as e:
            logging.error(f"GPSFabricConnector: Error sending coordinates: {e}")
            return False
