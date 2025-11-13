def penny_to_pounds__str(penny_amount):
    amount = penny_amount
    amount = str(amount)
    amount = amount[:-2] + '.' + amount[-2:]
    return (amount)
