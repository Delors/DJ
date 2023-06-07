import re
from binascii import unhexlify

from dj_ops import PerEntryTransformer


class DeHex(PerEntryTransformer):
    """Dehexes entries as used by Hashcat."""

    _re_hex = "\$HEX\[([a-fA-F0-9]+)\]"
    _m_hex = getHex = re.compile(_re_hex)

    def op_name() -> str: return "dehex"

    def process(self, entry: str) -> list[str]:
        try:    
            m = DeHex._m_hex.search(entry)
            if m:
                hex_term = m.group(1)
                unhexlified = unhexlify(hex_term).decode('utf-8')
                return [unhexlified]
        except:
            pass    
        return None


DEHEX = DeHex()
