import cv2
from pygcode import GCodeProgram, Line

# load the image
img = cv2.imread("square.png")

# convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# detect the edges of the shape in the image
edges = cv2.Canny(gray, 100, 200)

# find the contours of the shape
contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# create a new G-code program
prog = GCodeProgram()

# move to the starting position
prog += Line(x=0, y=0, z=0)

# draw the shape by following the contours
for contour in contours:
    for point in contour:
        x, y = point[0]
        prog += Line(x=x, y=y)

# write the G-code to a file
with open('output.gcode', 'w') as f:
    f.write(str(prog))
