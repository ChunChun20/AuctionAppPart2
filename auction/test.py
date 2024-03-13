from datetime import datetime

current_date = datetime.now()
current_date1 = datetime.strftime(current_date,"%m/%d/%Y, %H:%M:%S")

print(current_date1)