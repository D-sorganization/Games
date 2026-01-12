from PIL import Image

src = r"c:\Users\diete\Repositories\Games\launcher_assets\force_field_icon.png"
dst = r"c:\Users\diete\Repositories\Games\games\Force_Field\force_field_icon.ico"

try:
    img = Image.open(src)
    img.save(dst, format="ICO", sizes=[(256, 256)])
    print(f"Converted {src} to {dst}")
except Exception as e:
    print(f"Error: {e}")
