from ipaddress import IPv4Address, IPv6Address

from geoip2.database import Reader
from geoip2.errors import AddressNotFoundError

from app.models.proxy import Location


class GeoIP:
    """
    A wrapper around the GeoIP2 database for retrieving geolocation data.

    Attributes:
        reader (Reader): The GeoIP2 database reader instance.
    """

    def __init__(self, databasefile: str = "GeoLite2-City.mmdb") -> None:
        """
        Initialize the GeoIP instance with a GeoIP2 database file.

        Args:
            databasefile (str, optional): Path to the GeoIP2 database file. Defaults to "GeoLite2-City.mmdb".
        """
        self.reader = Reader(databasefile)

    def get_geolocation(self, ip: IPv4Address | IPv6Address) -> Location | None:
        """
        Retrieve geolocation information for a given IP address.

        Args:
            ip (IPv4Address | IPv6Address): The IP address to look up.

        Returns:
            Location | None: A Location object if geolocation data is available, otherwise None.
        """
        try:
            response = self.reader.city(ip)
        except AddressNotFoundError:
            return None

        if (
            not response.city.name
            or not response.subdivisions.most_specific.name
            or not response.country.iso_code
        ):
            return None

        return Location(
            city=response.city.name,
            region=response.subdivisions.most_specific.name,
            country_code=response.country.iso_code,
        )
