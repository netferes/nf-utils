import decimal
import math
from typing import Any, Literal, Union

MIN_WEI = 0
MAX_WEI = 2**256 - 1

units = {
    # EVM链单位
    "wei": decimal.Decimal("1"),
    "gwei": decimal.Decimal("1000000000"),
    "micro": decimal.Decimal("1000000000000"),
    "ether": decimal.Decimal("1000000000000000000"),

    # TRON单位
    "sun": decimal.Decimal("1000000"),
    "trx": decimal.Decimal("1000000000000000000"),
    
    # TON单位
    "nano": decimal.Decimal("1000000000"),
    "ton": decimal.Decimal("1000000000000000000"),
}

def is_integer(value: any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def from_wei(number: int, unit: str) -> decimal.Decimal:
    """
    Takes a number of wei and converts it to any other ether unit.
    """
    if unit.lower() not in units:
        raise ValueError(f"Unknown unit. Must be one of {'/'.join(units.keys())}")

    if number == 0:
        return decimal.Decimal(0)

    if number < MIN_WEI or number > MAX_WEI:
        raise ValueError("value must be between 0 and 2**256 - 1")

    unit_value = units[unit.lower()]

    with decimal.localcontext() as ctx:
        ctx.prec = 999
        d_number = decimal.Decimal(value=number, context=ctx)
        result_value = d_number / unit_value

    return result_value


def to_wei(number: Union[int, float, str, decimal.Decimal], unit: str) -> int:
    """
    Takes a number of a unit and converts it to wei.
    """
    if unit.lower() not in units:
        raise ValueError(f"Unknown unit. Must be one of {'/'.join(units.keys())}")

    if is_integer(number) or isinstance(number, str):
        d_number = decimal.Decimal(value=number)
    elif isinstance(number, float):
        d_number = decimal.Decimal(value=str(number))
    elif isinstance(number, decimal.Decimal):
        d_number = number
    else:
        raise TypeError("Unsupported type. Must be one of integer, float, or string")

    if d_number < MIN_WEI or d_number > MAX_WEI:
        raise ValueError("value must be between 0 and 2**256 - 1")
    
    s_number = str(number)
    unit_value = units[unit.lower()]

    if d_number == decimal.Decimal(0):
        return 0

    if d_number < 1 and "." in s_number:
        with decimal.localcontext() as ctx:
            multiplier = len(s_number) - s_number.index(".") - 1
            ctx.prec = multiplier
            d_number = decimal.Decimal(value=number, context=ctx) * 10**multiplier
        unit_value /= 10**multiplier

    with decimal.localcontext() as ctx:
        ctx.prec = 999
        result_value = decimal.Decimal(value=d_number, context=ctx) * unit_value
    
    if result_value > MAX_WEI:
        result_value = MAX_WEI
        
    if result_value < MIN_WEI or result_value > MAX_WEI:
        raise ValueError("Resulting wei value must be between 0 and 2**256 - 1")

    return int(result_value)


class Amount(decimal.Decimal):
    def __new__(
        cls,
        value: Union[int, float, str, decimal.Decimal],
        unit: Literal["ether", "trx", "wei", "gwei", "sun", "nano", "ton"] = "ether",
    ):
        if unit not in ["ether", "trx", "wei", "gwei", "sun", "nano", "ton"]:
            raise ValueError("unit must be one of 'ether','trx','wei','gwei','sun','nano','ton'")

        number = to_wei(value, unit)
        # from_wei 返回的是一个 Decimal 类型的值
        value = from_wei(number, "micro" if unit == "sun" else "ether")
        return super().__new__(cls, value)
    
    @property
    def value(self):
        return decimal.Decimal(self)
    
    @property
    def sun(self):
        return to_wei(self, "sun")

    @property
    def wei(self):
        return to_wei(self, "ether")
    
    @property
    def nano(self):
        return to_wei(self, "nano")
    
    @staticmethod
    def max() -> 'Amount':
        return Amount(MAX_WEI,"wei")
    
    @staticmethod
    def _parse(value: Union[int, float,str, decimal.Decimal,'Amount']) -> 'Amount':
        if isinstance(value,(int, float,str, decimal.Decimal)):
            return Amount(value)
        elif isinstance(value, Amount):
            return value
        else:
            raise ValueError("Unsupported type. Must be one of integer, float, string or Amount")
    
    def ceil(self,decimals:int=0) -> 'Amount':
        """根据小数点向上取整"""
        if decimals < 0:
            raise ValueError("decimals must be greater than or equal to 0")
        return Amount(math.ceil(self * 10**decimals) / 10**decimals)

    def __add__(self, x: Any) -> 'Amount':
        o = Amount._parse(x)
        return Amount(self.value + o.value)
    
    def __sub__(self, x: Any) -> 'Amount':
        o = Amount._parse(x)
        result = self.value - o.value
        return Amount(result if result > 0 else decimal.Decimal(0))
    
    def __mul__(self, x: Union[int,str, float,decimal.Decimal]) -> 'Amount':
        if isinstance(x,(float,int,str)) or isinstance(x,decimal.Decimal):
            result = self.value * decimal.Decimal(x)
            return Amount(result)
        else:
            raise TypeError("Unsupported type. Must be one of integer, float")
    
    def __truediv__(self, x: Union[int,float,str,decimal.Decimal]) -> 'Amount':
        if isinstance(x,(float,int,str)) or isinstance(x,decimal.Decimal):
            result = self.value / decimal.Decimal(x)
            return Amount(result)
        else:
            raise TypeError("Unsupported type. Must be one of integer, float")
        
    def __eq__(self, x: Any) -> bool:
        o = Amount._parse(x)
        return self.value == o.value
    
    def __ne__(self, x: Any) -> bool:
        o = Amount._parse(x)
        return self.value != o.value
    
    def __ge__(self, x: Any) -> bool:
        o = Amount._parse(x)
        return self.value >= o.value
    
    def __gt__(self, x: Any) -> bool:
        o = Amount._parse(x)
        return self.value > o.value
    
    def __le__(self, x: Any) -> bool:
        o = Amount._parse(x)
        return self.value <= o.value
    
    def __lt__(self, x: Any) -> bool:
        o = Amount._parse(x)
        return self.value < o.value
    
__all__ = ["Amount"]