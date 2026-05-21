"""
Devil ERP — Indian GST Calculator
Calculates CGST, SGST, IGST based on supply type
"""


def split_gst(rate: float, is_interstate: bool = False):
    """
    Returns dict: {cgst, sgst, igst, total_gst}
    """
    if is_interstate:
        return {"cgst": 0, "sgst": 0, "igst": rate, "total_gst": rate}
    half = rate / 2
    return {"cgst": half, "sgst": half, "igst": 0, "total_gst": rate}


def calculate_gst_on_amount(amount: float, rate: float, is_interstate: bool = False):
    """Returns (cgst_amt, sgst_amt, igst_amt, total_tax)"""
    split = split_gst(rate, is_interstate)
    total_tax = amount * (rate / 100)
    if is_interstate:
        return 0, 0, total_tax, total_tax
    half = total_tax / 2
    return half, half, 0, total_tax


def format_inr(amount: float) -> str:
    """₹ formatting with Indian comma style"""
    try:
        s = f"{abs(amount):,.2f}"
        parts = s.split(".")
        integer = parts[0].replace(",", "")
        # Indian grouping: last 3, then groups of 2
        if len(integer) > 3:
            last3 = integer[-3:]
            rest = integer[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            groups.reverse()
            integer = ",".join(groups) + "," + last3
        result = f"₹{integer}.{parts[1]}"
        return ("-" + result) if amount < 0 else result
    except Exception:
        return f"₹{amount:.2f}"
