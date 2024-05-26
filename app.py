import json
from flask import Flask, send_file
import requests
from PIL import Image
from io import BytesIO
import base64

app = Flask(__name__)

SKIN_SERVER_URL = "https://sessionserver.mojang.com/session/minecraft/profile/"
UUID_LOOKUP_URL = "https://api.mojang.com/users/profiles/minecraft/"


def get_skin_head(skin_url):
    response = requests.get(skin_url)
    image = Image.open(BytesIO(response.content))
    sub_image = image.crop((8, 8, 16, 16))

    if is_fully_transparent(sub_image):
        sub_image = image.crop((40, 8, 48, 16))
    else:
        hair_layer = image.crop((40, 8, 48, 16))
        combined = Image.new("RGBA", sub_image.size)
        combined.paste(sub_image, (0, 0))
        combined.paste(hair_layer, (0, 0), hair_layer)
        sub_image = combined

    zoomed_image = scale_image(sub_image)
    return zoomed_image


def is_fully_transparent(image):
    for pixel in image.getdata():
        if pixel[3] != 0:
            return False
    return True


def scale_image(image):
    new_size = (64, 64)
    return image.resize(new_size, Image.Resampling.NEAREST)


def get_skin_favicon(skin_content):
    skin_json = json.loads(skin_content)
    skin_url = skin_json['textures']['SKIN']['url']
    return get_skin_head(skin_url)


def get_skin_favicon_with_uuid(uuid):
    response = requests.get(SKIN_SERVER_URL + uuid)
    skin_result_json = response.json()
    decoded_skin_content = base64.b64decode(skin_result_json['properties'][0]['value']).decode('utf-8')
    return get_skin_favicon(decoded_skin_content)


def get_skin_favicon_with_username(username):
    response = requests.get(UUID_LOOKUP_URL + username)
    uuid_json = response.json()
    uuid = uuid_json['id']
    return get_skin_favicon_with_uuid(uuid)


@app.route('/name/<username>', methods=['GET'])
def skin_favicon_username(username):
    image = get_skin_favicon_with_username(username)
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/uuid/<uuid>', methods=['GET'])
def skin_favicon_uuid(uuid):
    image = get_skin_favicon_with_uuid(uuid)
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)
