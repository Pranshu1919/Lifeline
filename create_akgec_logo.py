from PIL import Image, ImageDraw, ImageFont
import math

def generate_akgec_logo():
    size = (600, 600)
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = 300, 300
    r_outer = 220
    r_inner = 140
    
    # Draw right side sunburst (yellow rays)
    num_rays = 12
    for i in range(num_rays):
        angle_deg = -75 + (i * 15)  # Right side arc (-90 to +90 degrees)
        angle_rad = math.radians(angle_deg)
        r1 = 150
        r2 = 250
        w = 12
        x1 = cx + r1 * math.cos(angle_rad)
        y1 = cy + r1 * math.sin(angle_rad)
        x2 = cx + r2 * math.cos(angle_rad)
        y2 = cy + r2 * math.sin(angle_rad)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 204, 0, 255), width=24)

    # Draw left side gear cog (black)
    num_teeth = 10
    for i in range(num_teeth):
        angle_deg = 100 + (i * 16)  # Left side arc (90 to 270 degrees)
        angle_rad = math.radians(angle_deg)
        x1 = cx + 150 * math.cos(angle_rad)
        y1 = cy + 150 * math.sin(angle_rad)
        x2 = cx + 220 * math.cos(angle_rad)
        y2 = cy + 220 * math.sin(angle_rad)
        draw.line([(x1, y1), (x2, y2)], fill=(20, 20, 20, 255), width=20)
        
    # Draw central split circle
    draw.chord([cx-150, cy-150, cx+150, cy+150], 90, 270, fill=(20, 20, 20, 255))
    draw.chord([cx-150, cy-150, cx+150, cy+150], -90, 90, fill=(255, 204, 0, 255))

    # Inner core circle (white/transparent cutout)
    draw.ellipse([cx-70, cy-70, cx+70, cy+70], fill=(255, 255, 255, 255))
    draw.ellipse([cx-40, cy-40, cx+40, cy+40], fill=(20, 20, 20, 255))

    # Curved arc text on left
    draw.arc([cx-210, cy-210, cx+210, cy+210], 110, 250, fill=(20, 20, 20, 255), width=8)

    img.save("akgec_logo.png")
    print("Generated akgec_logo.png successfully")

if __name__ == "__main__":
    generate_akgec_logo()
