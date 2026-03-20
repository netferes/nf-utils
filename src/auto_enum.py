from enum import Enum, auto


def parse(cls, value: any, defalut=None):
    if isinstance(value, cls):
        return value
    if isinstance(value, str) and value.lower() in {e.value for e in cls}:
        return cls(value.lower())
    return defalut if defalut else getattr(cls, "UNKNOW", None)
    
class AutoName(Enum):
    value: str

    def _generate_next_value_(self, *args):
        return self.lower()

    def __repr__(self):
        return f"backend.enums.{self}"
