from PIL import Image, ImageDraw, ImageFont
import os
import sys

def create_icon(name: str, color: tuple, size: tuple = (64, 64)) -> None:
    """
    Create a simple icon with text
    
    Args:
        name: Icon name (will be used as text)
        color: RGB color tuple
        size: Icon size tuple (width, height)
    """
    try:
        # Create image with white background
        image = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw colored circle
        circle_radius = min(size) // 2 - 4
        circle_center = (size[0] // 2, size[1] // 2)
        draw.ellipse(
            (
                circle_center[0] - circle_radius,
                circle_center[1] - circle_radius,
                circle_center[0] + circle_radius,
                circle_center[1] + circle_radius
            ),
            fill=color
        )
        
        # Use default font
        font = ImageFont.load_default()
        
        # Calculate text position to center it
        text_bbox = draw.textbbox((0, 0), name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = (
            (size[0] - text_width) // 2,
            (size[1] - text_height) // 2
        )
        
        # Draw text
        draw.text(text_position, name, fill='white', font=font)
        
        # Save icon
        output_path = os.path.join(os.path.dirname(__file__), f"{name}.png")
        image.save(output_path)
        print(f"Created {output_path}")
        
    except Exception as e:
        print(f"Error creating {name}.png: {str(e)}", file=sys.stderr)
        raise

def main():
    """Generate all required icons"""
    try:
        # Define icons to create
        icons = {
            "login": (74, 144, 226),      # Blue
            "register": (46, 204, 113),   # Green
            "app": (52, 152, 219),        # Light Blue
            "new": (46, 204, 113),        # Green
            "open": (52, 152, 219),       # Light Blue
            "save": (155, 89, 182),       # Purple
            "exit": (231, 76, 60),        # Red
            "cut": (230, 126, 34),        # Orange
            "copy": (52, 152, 219),       # Light Blue
            "paste": (46, 204, 113),      # Green
            "about": (52, 73, 94)         # Dark Blue
        }
        
        # Create icons directory if it doesn't exist
        os.makedirs(os.path.dirname(__file__), exist_ok=True)
        
        # Generate icons
        for name, color in icons.items():
            create_icon(name, color)
            
    except Exception as e:
        print(f"Error in main: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 