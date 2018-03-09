"""Define all Palo Alto Networks actions."""
from plugins.interfaces import Ip


class PaloAltoNetworks(Ip):
    """Palo Alto Networks IP address object."""
    def __init__(self, ipaddr, reason):
        self.ipaddr = ipaddr
        self.reason = reason

    def add_to_ebl(self):
        """Add to BanHammer's External Block List for PAN firewalls."""
        # no need to do anything as EBL's are hosted on BanHammer
        pass
