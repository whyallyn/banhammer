"""Define all Palo Alto Networks actions."""
from plugins.interfaces import Domain


class PaloAltoNetworks(Domain):
    """Palo Alto Networks URL object."""
    def __init__(self, domain, reason):
        self.domain = domain
        self.reason = reason

    def add_to_ebl(self):
        """Add to BanHammer's External Block List for PAN firewalls."""
        # no need to do anything as EBL's are hosted on BanHammer
        pass
