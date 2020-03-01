import sys
sys.path = ['/opt/python/current/app', '/opt/python/run/venv/local/lib64/python3.6/site-packages', '/opt/python/run/venv/local/lib/python3.6/site-packages', '/opt/python/run/venv/lib64/python3.6', '/opt/python/run/venv/lib/python3.6', '/opt/python/run/venv/lib64/python3.6/site-packages', '/opt/python/run/venv/lib/python3.6/site-packages', '/opt/python/run/venv/lib64/python3.6/lib-dynload', '/opt/python/run/venv/local/lib/python3.6/dist-packages', '/usr/lib64/python3.6', '/usr/lib/python3.6', '/opt/python/run/venv/lib64/python3.6/dist-packages/']
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
    utils.save_image(output_image, output[0])




application = Flask(__name__)
application.secret_key = b"g\xfe\xd4\xac\x19U\xc7\x14\xa89\x89/'F\xd5a"

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
USERFILES_DIRECTORY = os.path.join(STATIC_DIRECTORY, 'user_files')

def downloadDirectoryFroms3(bucketName,remoteDirectoryName):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucketName) 
    for object in bucket.objects.filter(Prefix = remoteDirectoryName):
        print(object.key)
        dest = os.path.join(STATIC_DIRECTORY, str(object.key))
        print(dest)
        bucket.download_file(object.key, dest)

print("Static Dir:", STATIC_DIRECTORY)
if len(os.listdir(os.path.join(STATIC_DIRECTORY,"offeredStyles"))) == 0:
    downloadDirectoryFroms3('seng6285-project', 'offeredStyles')

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

def loadDataForUser(user, secret):

#     dynDB = boto3.resource('dynamodb')
#     table = dynDB.Table('stylizer_records')
#     uid = request.cookies.get('uid')
#     response = table.query(
#         KeyConditionExpression=Key('uid').eq(uid) & Key('secret').eq(request.cookies.get('secret'))
#     )
#     data = []
#     for item in response:

# Loading from JSON for now.
    data = []
    if os.path.exists("urls.json"):
        with open('urls.json', 'r') as url_file:
            urls = json.load(url_file)
        if user in urls.keys():
            if secret in urls[user].keys():
                data = urls[user][secret]
    return data
        
    

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

    return render_template('style_image.html')

@application.route('/proc', methods=['POST'])
def proc():
    # Was using this section as a test function to iterate through AWS integration.
    # Below is jumbled junk at the moment

    # Record into DynamoDB
    # dynDB = boto3.resource('dynamodb')
    # table = dynDB.Table('stylizer_records')
    # response = table.put_item(
    #     Item={
    #         'guid':str(uuid.uuid1()),
    #         'uid':request.cookies.get('uid'),
    #         'secret':request.cookies.get('secret'),
    #         'style': request.form['convertStyle'],
    #         's3-image-path':'seng6285-project/' + secure_filename(f.filename),
    #         's3-product-url':None
    #     }
    # )
    # record user, secret, style, s3-image-url, s3-product-url (as "in-process") to dynamodb
    # call method with style
    # move output to s3
    userID = request.cookies.get('uid')
    userKey = request.cookies.get('secret')

    urls = {}
    # Loads json - block won't exist in RDS version
    if os.path.exists('urls.json'):
        with open('urls.json', 'r') as url_file:
            urls = json.load(url_file)


    # File into S3:
    # Need to set up your AWSCLI and run 'aws config' before this will work
    # s3 = boto3.resource('s3')
    # f = request.files['file']
    # filename = request.form['convertStyle'] + "_" + secure_filename(f.filename)
    # s3.Bucket('seng6285-project').put_object(Key=filename, Body=f)


    # Remove json and local file version of this when connected to AWS
    f = request.files['file']
    save_name = request.form['convertStyle'] + secure_filename(f.filename)
    f.save(os.path.join(USERFILES_DIRECTORY, save_name))
    stylize(os.path.join(USERFILES_DIRECTORY, save_name), os.path.join(USERFILES_DIRECTORY, "out_" + save_name), os.path.join(STATIC_DIRECTORY, "offeredStyles", request.form['convertStyle'] + ".pth"))
    if userID not in urls.keys():
        urls[userID] = {}
    if userKey not in urls[userID].keys():
        urls[userID][userKey] = []

    urls[userID][userKey].append({'name': secure_filename(f.filename), 'style':request.form['convertStyle'], 'url':url_for('static', filename='user_files/out_' + save_name)})

    with open('urls.json', 'w') as url_file:
        json.dump(urls, url_file)

    return redirect(url_for('home'))

@application.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


if __name__ == '__main__':
    application.run(host='0.0.0.0')
