import torch
from PIL import Image


def load_image(filename, size=None, scale=None):
    img = Image.open(filename).convert(mode='RGB')
    
    if img.size[0] > 1200 or img.size[1] > 1200:
        scale = 1200 / max(img.size[0], img.size[1])
    if size is not None:
        img = img.resize((size, size), Image.ANTIALIAS)
    elif scale is not None:
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.ANTIALIAS)
    return img


def save_image(data, filename=None, stream=None):
    img = data.clone().clamp(0, 255).numpy()
    img = img.transpose(1, 2, 0).astype("uint8")
    img = Image.fromarray(img)
    if stream is None:
        print("img save file")
        img.save(filename)
    else:
        print("img save stream")
        img.save(stream, format="png")

def resize(instream, outstream):
    load_image(instream).save(outstream, format="png")


def gram_matrix(y):
    (b, ch, h, w) = y.size()
    features = y.view(b, ch, w * h)
    features_t = features.transpose(1, 2)
    gram = features.bmm(features_t) / (ch * h * w)
    return gram


def normalize_batch(batch):
    # normalize using imagenet mean and std
    mean = batch.new_tensor([0.485, 0.456, 0.406]).view(-1, 1, 1)
    std = batch.new_tensor([0.229, 0.224, 0.225]).view(-1, 1, 1)
    batch = batch.div_(255.0)
    return (batch - mean) / std
