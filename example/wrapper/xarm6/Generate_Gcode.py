import cv2

# Load image
img = cv2.imread('./Bunny.jpg')

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Threshold image to remove noise
thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

contour_image = cv2.drawContours(img, contours, -1, (0,255,0),3)

cv2.imshow('Contours', contour_image)

# Generate G-code commands for each contour
"""gcode = ""
for contour in contours:
    for point in contour:
        x, y = point[0]
        gcode += "G01 X{} Y{}\n".format(x, y)

# Save G-code to a file
with open('./output.gcode', 'w') as f:
    f.write(gcode)"""
