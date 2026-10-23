from sqlalchemy import Numeric

# Use Decimal in Python and decimal strings in JSON. Never persist money as float.
MONEY = Numeric(precision=18, scale=2, asdecimal=True)
