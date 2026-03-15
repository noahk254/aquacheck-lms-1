import io
import base64
import qrcode
from qrcode.image.pure import PyPNGImage


def generate_barcode(sample_code: str) -> str:
    """Generate a QR code for the given sample_code and return a base64-encoded PNG string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(sample_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded
