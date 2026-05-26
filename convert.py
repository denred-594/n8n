from PIL import Image
import numpy as np
import cv2
import os

def jpg_to_vector_svg(input_jpg, output_svg, threshold=128):
    # Read the image
    img = cv2.imread(input_jpg, cv2.IMREAD_GRAYSCALE)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create SVG
    height, width = img.shape
    with open(output_svg, 'w') as f:
        f.write(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n')
        f.write('<path d="')
        
        for contour in contours:
            if len(contour) > 1:  # Need at least 2 points to draw a line
                # Move to first point
                x, y = contour[0][0]
                f.write(f'M{x},{y} ')
                
                # Draw lines to subsequent points
                for point in contour[1:]:
                    x, y = point[0]
                    f.write(f'L{x},{y} ')
                
                # Close the path
                f.write('Z ')
        
        f.write('" fill="black" stroke="none"/>\n')
        f.write('</svg>')

# Example usage
jpg_to_vector_svg('img39.jpg', 'output_vector.svg')