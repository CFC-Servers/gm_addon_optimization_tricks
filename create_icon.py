from PIL import Image, ImageDraw
import math

BG_COLOR = "#2a2a2a"
ACCENT_COLOR = "#2a82da"


def create_icon(size: int = 256,
                bg_color: str = BG_COLOR,
                accent_color: str = ACCENT_COLOR,
                out_path: str = "icon.png"):
    # draw at higher resolution for better downscale quality
    img = Image.new("RGB", (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)

    center = size // 2
    outer_radius = 90
    inner_radius = 60
    tooth_width = 15

    for i in range(8):
        angle = i * 45
        left = math.radians(angle - tooth_width)
        right = math.radians(angle + tooth_width)

        points = [
            (center + int(inner_radius * math.cos(left)), center + int(inner_radius * math.sin(left))),
            (center + int(outer_radius * math.cos(left)), center + int(outer_radius * math.sin(left))),
            (center + int(outer_radius * math.cos(right)), center + int(outer_radius * math.sin(right))),
            (center + int(inner_radius * math.cos(right)), center + int(inner_radius * math.sin(right))),
        ]
        draw.polygon(points, fill=accent_color)

    # center ring and hub
    draw.ellipse([
        center - inner_radius, center - inner_radius,
        center + inner_radius, center + inner_radius
    ], fill=accent_color)
    draw.ellipse([
        center - 30, center - 30,
        center + 30, center + 30
    ], fill=bg_color)

    # only produce a 64x64 icon
    img_64 = img.resize((64, 64), Image.Resampling.LANCZOS)
    img_64.save(out_path)

    return out_path


if __name__ == "__main__":
    icon_path = create_icon()
    print(f"Icon created: {icon_path}")
