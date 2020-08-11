#!/usr/bin/env python3
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

fig = plt.figure()
ax = plt.axes(projection="3d")

x = [1,2]
y = [2,3]
z = [5,6]
a = [[1, 2, 5], [2, 3, 6]]


x = [x for x in zip(*a)][0]
y = [x for x in zip(*a)][1]
z = [x for x in zip(*a)][2]


ax.plot3D(x,y,z)
ax.set_xlabel('X Axes')
ax.set_ylabel('Y Axes')
ax.set_zlabel('Z Axes')

plt.show()
