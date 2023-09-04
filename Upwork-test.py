from sanic import Sanic
from sanic.response import HTTPResponse
import aiohttp
import asyncio
import io
from PIL import Image


app = Sanic(__name__)

async def fetch_image(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    # Open the image using Pillow
                    image = Image.open(io.BytesIO(image_data))
                    # Resize the image to 32x32 pixels
                    image = image.resize((32, 32), Image.ANTIALIAS)
                    # Convert the image back to bytes
                    with io.BytesIO() as byte_io:
                        image.save(byte_io, format='JPEG')
                        return byte_io.getvalue()
                elif response.status == 404:
                    # Return a black tile for missing images
                    return b'\x00' * 32 * 32 * 3
    except Exception as e:
        # Return a blue tile for any other errors
        return b'\x00\x00\xFF' * 32 * 32

async def fetch_all_images():
    urls = [f"https://api.slingacademy.com/public/sample-photos/{i}.jpeg" for i in range(1, 133)]
    images = await asyncio.gather(*[fetch_image(url) for url in urls])
    return images

def create_composite_image(images, rows, cols):
    image_size = (32, 32)
    composite = Image.new('RGB', (cols * image_size[0], rows * image_size[1]))

    for i, image_data in enumerate(images):
        if image_data is not None:
            image = Image.open(io.BytesIO(image_data))
        else:
            # Create a black tile for missing images
            image = Image.new('RGB', image_size)

        col = i % cols
        row = i // cols
        composite.paste(image, (col * image_size[0], row * image_size[1]))

    return composite

@app.route("/")
async def serve_composite_image(request):
    rows, cols = 12, 11  # Assuming a grid layout
    images = await fetch_all_images()
    composite = create_composite_image(images, rows, cols)

    # Convert the composite image to bytes
    with io.BytesIO() as byte_io:
        composite.save(byte_io, format='JPEG')
        image_bytes = byte_io.getvalue()

    return HTTPResponse(body=image_bytes, content_type='image/jpeg')

if __name__ == "__main__":
    app.config.DEBUG = True
    app.run(host="0.0.0.0", port=8000)