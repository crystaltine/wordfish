import matplotlib.pyplot as plt
import random

csvdata = open('queryfiles/a-general-monthly-d504b98c.csv', 'r')
data = csvdata.readlines()

timestamps = data[0]
# prune names from the beginnings of the lines
for line in range(1, len(data)):
    data[line] = data[line].split(',')[1:]
    map(lambda x: int(x), data[line])
    
for row in range(1, len(data)):
    randomcolor = (random.random(), random.random(), random.random())
    plt.bar(timestamps, data[row], label=data[row][0], color=randomcolor)
    
plt.legend()
plt.show()