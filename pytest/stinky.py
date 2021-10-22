



x = """
https://en.wikipedia.org/wiki/Bulgaria
""".lower()

amap = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine"
}

y = ""
for char in x:
    if char in "qwertyuiopasdfghjklzxcvbnm":
        y += f":regional_indicator_{char}: "
    elif char in "1234567890":
        y += f":{amap[int(char)]}: "
    else:
        y += char




print(y)











