import logging

from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

src = r"c:\Users\diete\Repositories\Games\launcher_assets\force_field_icon.png"
dst = r"c:\Users\diete\Repositories\Games\games\Force_Field\force_field_icon.ico"

try:
    img = Image.open(src)
    img.save(dst, format="ICO", sizes=[(256, 256)])
    logger.info("Converted %s to %s", src, dst)
except Exception as e:
    logger.error("Error: %s", e)
