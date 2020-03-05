import sys
from os import environ
#print("Flask_env=",environ['FLASK_ENV'])
if 'FLASK_ENV' not in environ.keys() or environ['FLASK_ENV'] != 'development':
    sys.path = ['/opt/python/current/app', '/opt/python/run/venv/local/lib64/python3.6/site-packages', '/opt/python/run/venv/local/lib/python3.6/site-packages', '/opt/python/run/venv/lib64/python3.6', '/opt/python/run/venv/lib/python3.6', '/opt/python/run/venv/lib64/python3.6/site-packages', '/opt/python/run/venv/lib/python3.6/site-packages', '/opt/python/run/venv/lib64/python3.6/lib-dynload', '/opt/python/run/venv/local/lib/python3.6/dist-packages', '/usr/lib64/python3.6', '/usr/lib/python3.6', '/opt/python/run/venv/lib64/python3.6/dist-packages/']
else:
    print(str(sys.path))

    print("Didn't set path")
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, make_response
import json
import os.path
from werkzeug.utils import secure_filename
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
from RandomNamer import RandomNamer
import string
import random
import utils
import torch
from torchvision import transforms
from transformer_net import TransformerNet
import re
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

BUCKET_NAME = 'seng6285-project'

def stylize(content_image, output_image, model):
    device = torch.device("cpu")

    # Check for scale
    content_image = utils.load_image(content_image)
    content_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])
    content_image = content_transform(content_image)
    content_image = content_image.unsqueeze(0).to(device)

    with torch.no_grad():
        style_model = TransformerNet()
        state_dict = torch.load(model)
        # remove saved deprecated running_* keys in InstanceNorm from the checkpoint
        for k in list(state_dict.keys()):
            if re.search(r'in\d+\.running_(mean|var)$', k):
                del state_dict[k]
        style_model.load_state_dict(state_dict)
        style_model.to(device)
        output = style_model(content_image).cpu()
    if isinstance(output_image, str):
        print("Util Save File")
        utils.save_image(filename=output_image, data=output[0])
    elif isinstance(output_image, BytesIO):
        print("Util write stream")
        utils.save_image(data=output[0], stream=output_image)




application = Flask(__name__)
application.secret_key = b"g\xfe\xd4\xac\x19U\xc7\x14\xa89\x89/'F\xd5a"

application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin6285:Group2BDJMN@stylizer-db.cyp8zfafgxaq.us-east-1.rds.amazonaws.com/seng'

db = SQLAlchemy(application)

class user_data(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(45))
    imagename = db.Column(db.String(45))
    secret = db.Column(db.String(45))
    date = db.Column(db.DateTime, default=datetime.now)
    style = db.Column(db.String(45))
    sourceuri = db.Column(db.String(2000))
    producturi = db.Column(db.String(2000))


STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
# USERFILES_DIRECTORY = os.path.join(STATIC_DIRECTORY, 'user_files')

def downloadDirectoryFromS3(bucketName,remoteDirectoryName):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucketName) 
    for object in bucket.objects.filter(Prefix = remoteDirectoryName):
        print(object.key)
        dest = os.path.join(STATIC_DIRECTORY, str(object.key))
        print(dest)
        bucket.download_file(object.key, dest)

#print("Static Dir:", STATIC_DIRECTORY)
if len(os.listdir(os.path.join(STATIC_DIRECTORY,"offeredStyles"))) == 0:
    downloadDirectoryFromS3(BUCKET_NAME, 'offeredStyles')

@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@application.route('/')
def home():
    uid = request.cookies.get('uid')
    secret = request.cookies.get('secret')
    images = []
    if uid == None:
        uid = RandomNamer.getName()
        secret = randomString()
        resp = make_response(redirect(url_for('home')))
        resp.set_cookie('uid', value=uid, max_age=60*60*24*365*2)
        resp.set_cookie('secret', value=secret, max_age=60*60*24*365*2)
        return resp
    else:
        images = loadDataForUser(uid, secret)


    return render_template('home.html', images=images, uid=uid, secret=secret)

def loadDataForUser(userID, userKey):
    return user_data.query.filter(user_data.user==userID).filter(user_data.secret==userKey).all()

@application.route('/set-id', methods=['POST'])
def set_id():
    uid = request.cookies.get('uid')
    newuid = request.form['newuid']
    secret = request.form['secret']
    resp = make_response(render_template('set_id.html', uid=uid, newuid=newuid, secret=secret))
    return resp

@application.route('/update-id', methods=['POST'])
def update_id():
    newuid = request.form['newuid']
    newsecret = request.form['newsecret']
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('uid', value=newuid, max_age=60*60*24*365*2)
    resp.set_cookie('secret', value=newsecret, max_age=60*60*24*365*2)
    return resp

@application.route('/style-new')
def style_new():
    uid = request.cookies.get('uid')
    return render_template('style_image.html', uid=uid)

# @application.route('/ptest', methods=['POST'])
# def procTest():
#     f = request.files['file']
#     f.save("Chuck.png")
#     save_name = 'test.png'
#     myBytes = BytesIO()
#     stylize(f, myBytes, os.path.join(STATIC_DIRECTORY, "offeredStyles", request.form['convertStyle'] + ".pth"))
#     with open(save_name, 'wb') as fp:
#         fp.write(myBytes.getvalue())
#     stylize("Chuck.png", "test2.png", os.path.join(STATIC_DIRECTORY, "offeredStyles", request.form['convertStyle'] + ".pth"))
#     return redirect(url_for('style_new'))
    

@application.route('/proc', methods=['POST'])
def proc():
    # Pull out all the components of the form
    userID = request.cookies.get('uid')
    userKey = request.cookies.get('secret')
    f = request.files['file']
    style = request.form['convertStyle']
    filename = secure_filename(f.filename)
    # Change extension to png
    pre, ext = os.path.splitext(filename)
    pngFilename = f"{pre}.png"    

    sourceFileName = f"user_data/{userID}/{filename}"
    destFileName = f"user_data/{userID}/{style}_{pngFilename}"
    
    sourceURL = f"http://s3.us-east-1.amazonaws.com/{BUCKET_NAME}/{sourceFileName}"
    # File into S3:
    # Need to set up your AWSCLI and run 'aws config' before this will work
    s3 = boto3.resource('s3')
    # Save original
    s3.Bucket(BUCKET_NAME).put_object(Key=sourceFileName, Body=f)

    # Create user_data row, no sourceURL
    newData = user_data(user=userID, secret=userKey, imagename=filename, style=style,sourceuri=sourceURL, producturi=None)
    db.session.add(newData)
    db.session.commit()
    
    # Stylize
    myBytes = BytesIO()
    stylize(f, myBytes, os.path.join(STATIC_DIRECTORY, "offeredStyles", f"{style}.pth"))

    # Save Product
    s3.Bucket(BUCKET_NAME).put_object(Key=destFileName, Body=myBytes.getvalue())
    
    # Update Product item
    newData.producturi = f"http://s3.us-east-1.amazonaws.com/{BUCKET_NAME}/{destFileName}"
    db.session.commit()
    
    return redirect(url_for('home'))

@application.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', uid=uid), 404

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


if __name__ == '__main__':
    application.run(host='0.0.0.0')
