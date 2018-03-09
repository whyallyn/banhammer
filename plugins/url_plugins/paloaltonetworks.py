"""Define all Palo Alto Networks actions."""
from plugins.interfaces import Url


class PaloAltoNetworks(Url):
    """Palo Alto Networks URL object."""
    def __init__(self, url, reason):
        self.url = url
        self.reason = reason

    def add_to_ebl(self):
        """Add to BanHammer's External Block List for PAN firewalls."""
        # no need to do anything as EBL's are hosted on BanHammer
        pass
