"""Amazon marketplace IDs and the SP-API region each one belongs to.

https://developer-docs.amazon/sp-api/docs/marketplace-ids
"""

from enum import Enum


class Region(str, Enum):
    NA = "NA"  # North America
    EU = "EU"  # Europe, Middle East, India
    FE = "FE"  # Far East


class Marketplace(Enum):
    """Marketplace -> (marketplace_id, region)."""

    # North America
    US = ("ATVPDKIKX0DER", Region.NA)
    CA = ("A2EUQ1WTGCTBG2", Region.NA)
    MX = ("A1AM78C64UM0Y8", Region.NA)
    BR = ("A2Q3Y263D00KWC", Region.NA)
    # Europe / Middle East / India
    IE = ("A28R8C7NBKEWEA", Region.EU)
    ES = ("A1RKKUPIHCS9HS", Region.EU)
    UK = ("A1F83G8C2ARO7P", Region.EU)
    FR = ("A13V1IB3VIYZZH", Region.EU)
    BE = ("AMEN7PMS3EDWL", Region.EU)
    NL = ("A1805IZSGTT6HS", Region.EU)
    DE = ("A1PA6795UKMFR9", Region.EU)
    IT = ("APJ6JRA9NG5V4", Region.EU)
    SE = ("A2NODRKZP88ZB9", Region.EU)
    ZA = ("AE08WJ6YKNBMC", Region.EU)
    PL = ("A1C3SOZRARQ6R3", Region.EU)
    EG = ("ARBP9OOSHTCHU", Region.EU)
    TR = ("A33AVAJ2PDY3EV", Region.EU)
    SA = ("A17E79C6D8DWNP", Region.EU)
    AE = ("A2VIGQ35RCS4UG", Region.EU)
    IN = ("A21TJRUUN4KGV", Region.EU)
    # Far East
    SG = ("A19VAU5U5O7RUS", Region.FE)
    AU = ("A39IBJ37TRP1C6", Region.FE)
    JP = ("A1VC38T7YXB528", Region.FE)

    @property
    def marketplace_id(self) -> str:
        return self.value[0]

    @property
    def region(self) -> Region:
        return self.value[1]
