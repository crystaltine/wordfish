import datetime

date1 = datetime.datetime(2020, 1, 1, 0, 0, 0)
datetarget = datetime.datetime(2023, 6, 16, 0, 0, 0)

def _advance_one_month(d: datetime.datetime):
    if d.month == 12:
        return d.replace(year=d.year+1, month=1)
    return d.replace(month=d.month+1)
while date1 != datetarget.replace(day=1):
    print(date1)
    date1 = _advance_one_month(date1)