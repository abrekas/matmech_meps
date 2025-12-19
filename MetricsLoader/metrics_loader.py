from itertools import count

loaded = ""
with open("..\\Matmekh.Maps\\Matmekh.Maps\\Infrastructure\\metric.txt", "r") as file:
    loaded = file.read()
result = {}
for data in loaded.split(";"):
    if data == "":
        continue
    date, time = data.split()
    day, start_time = date.split("T")

    is_good = False

    if 6000 <= int(time) <= 12000:
        is_good = True

    if day in result.keys():
        if is_good:
            result[day]["good"] += 1
        else:
            result[day]["bad"] += 1
    else:
        result[day] = {"good": 0, "bad": 0}
        if is_good:
            result[day]["good"] += 1
        else:
            result[day]["bad"] += 1
print(result)
for date in result.keys():
    if result[date]['bad'] == 0:
        if result[date]['good'] == 0:
            print(date, "нет данных")
        else:
            print(date, "100%")
        continue
    print(date, f"{result[date]['good']/result[date]['bad']}%")