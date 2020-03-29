import sys
from os import environ
#print("Flask_env=",environ['FLASK_ENV'])
if 'UPSTART_JOB' in environ.keys():
    sys.path = ['/opt/python/current/app', '/opt/python/run/venv/local/lib64/python3.6/site-packages', '/opt/python/run/venv/local/lib/python3.6/site-packages', '/opt/python/run/venv/lib64/python3.6', '/opt/python/run/venv/lib/python3.6', '/opt/python/run/venv/lib64/python3.6/site-packages', '/opt/python/run/venv/lib/python3.6/site-packages', '/opt/python/run/venv/lib64/python3.6/lib-dynload', '/opt/python/run/venv/local/lib/python3.6/dist-packages', '/usr/lib64/python3.6', '/usr/lib/python3.6', '/opt/python/run/venv/lib64/python3.6/dist-packages/']
else:
    print(str(sys.path))

    print("Didn't set path")
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, make_response, send_from_directory
import json
import os.path
from werkzeug.utils import secure_filename
import boto3
from boto3.dynamodb.conditions import Key, Attr
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
from KaraokeQueue import KaraokeQueue
import atexit
import threading

application = Flask(__name__)
application.secret_key = b"g\xfe\xd4\xac\x19U\xc7\x14\xa89\x89/'F\xd5a"

with open("db.uri", 'r') as fp:
    application.config['SQLALCHEMY_DATABASE_URI'] = fp.readline()
    
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
        #print("Util Save File")
        utils.save_image(filename=output_image, data=output[0])
    elif isinstance(output_image, BytesIO):
        #print("Util write stream")
        utils.save_image(data=output[0], stream=output_image)

def downloadDirectoryFromS3(bucketName,remoteDirectoryName):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucketName) 
    for object in bucket.objects.filter(Prefix = remoteDirectoryName):
        print(object.key)
        dest = os.path.join(STATIC_DIRECTORY, str(object.key))
        print(dest)
        bucket.download_file(object.key, dest)

@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@application.route('/')
def Index(InitialRoute = 'v-pills-home'):
    temp = request.args.get('InitialRoute')
    if temp:
        InitialRoute = temp
    uid = request.cookies.get('uid')
    if uid == None:
        uid = RandomNamer.getName()
        secret = randomString()
        resp.set_cookie('uid', value=uid, max_age=60*60*24*365*2)
        resp.set_cookie('secret', value=secret, max_age=60*60*24*365*2)
    return render_template('base.html', uid=uid, IR=InitialRoute)

@application.route('/home')
def home():
    return render_template('home.html')

@application.route('/Feedback', methods=['POST'])
def Feedback():
    return redirect(url_for('Index'))

@application.route('/GettingStarted')
def GettingStarted():
    return render_template('GettingStarted.html')

@application.route('/About')
def About():
    return render_template('AboutUs.html')

@application.route('/UserImages')
def UserImages():
    return render_template('Images.html')

@application.route('/UserResults')
def UserResults():
    uid = request.cookies.get('uid')
    images = []
    if uid != None:
        secret = request.cookies.get('secret')
        images = loadDataForUser(uid, secret)
    return render_template('Results.html', images=images)

def loadDataForUser(userID, userKey):
    return user_data.query.filter(user_data.user==userID).filter(user_data.secret==userKey).all()

@application.route('/set-id', methods=['GET'])
def set_id():
    uid = request.cookies.get('uid')
    secret = request.cookies.get('secret')
    resp = make_response(render_template('set_id.html', uid=uid, newuid=uid, secret=secret))
    return resp

@application.route('/update-id', methods=['POST'])
def update_id():
    newuid = request.form['newuid']
    newsecret = request.form['newsecret']
    resp = make_response(redirect(url_for('Index', InitialRoute='v-pills-settings')))
    resp.set_cookie('uid', value=newuid, max_age=60*60*24*365*2)
    resp.set_cookie('secret', value=newsecret, max_age=60*60*24*365*2)
    return resp    

@application.route('/proc', methods=['POST'])
def proc():
    # Pull out all the components of the form
    userID = request.cookies.get('uid')
    userKey = request.cookies.get('secret')
    f = request.files['file']
    style = request.form['convertStyle']
    
    # Change extension to png
    pre, ext = os.path.splitext(secure_filename(f.filename))
    pngFilename = f"{pre}.png"    

    sourceFileName = f"user_data/{userID}/{pngFilename}"
    

    # Think before we act:
    # 1. The source needs to be saved AND we need to run the operation. (regular case)
    # 2. The file failed to save, but the order could already be submitted (try resaving file)
    # 3. The file could be the same, so we can skip saving source.  (need to submit order)    
    # 4. The file is saved, the order is submitted.  (Skip everything, duplicate order)
    
    isFileSaved = False
    # File into S3:
    # Need to set up your AWSCLI and run 'aws config' before this will work
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    objs = list(bucket.objects.filter(Prefix=sourceFileName))
    if len(objs) > 0 and objs[0].key == sourceFileName:
        isFileSaved = True # cases 3,4
    else:
        # Save original
        # Cases 1,2
        fileAsPng = BytesIO()
        utils.resize(f, fileAsPng)
        bucket.put_object(Key=sourceFileName, Body=fileAsPng.getvalue())

    # Check for existing record, duplicate returns 
    record, isSubmitted = initialize_record(userID, userKey, pngFilename, style)

    if isSubmitted and isFileSaved: # case 4
        flash("Request identical to one of your previous submissions.", "bg-danger")
        return redirect(url_for('Index',InitialRoute='v-pills-Results'))
    
    

    processQueue.add(record)
    flash("Image submitted","bg-success")
    
    return redirect(url_for('Index',InitialRoute='v-pills-Results'))

def initialize_record(user, key, filename, style):
    dupCheck = user_data.query.filter(user_data.user==user).filter(user_data.secret==key).filter(user_data.style==style).filter(user_data.imagename==filename).all()    
    if len(dupCheck) > 0:
        return dupCheck[0], True

    # Create user_data row, no producturi because we haven't created it yet
    sourceURL = f"http://s3.us-east-1.amazonaws.com/{BUCKET_NAME}/user_data/{user}/{filename}"
    newData = user_data(user=user, secret=key, imagename=filename, style=style,sourceuri=sourceURL, producturi="In Queue")
    db.session.add(newData)
    db.session.commit()
    return newData, False

import time

def run_transformer():
    #print("Transformer loop started")

    #total = user_data.query.all()
    #print(f"Found {len(total)} total records")

    #unfinished_Old = user_data.query.filter(user_data.producturi==None).all()
    #print(f"Found {len(unfinished_Old)} old unfinished records")
    # for record in unfinished_Old:
        # processQueue.add(record)

    unfinished_New = user_data.query.filter(user_data.producturi=='In Queue').all()
    print(f"Found {len(unfinished_New)} New unfinished records")
    for record in unfinished_New:
        processQueue.add(record)


    while not stopRequested:
        if not processQueue.hasItems():            
            #print("Transformer sleeping")
            time.sleep(5)
        else:
            transform(processQueue.next())
    
    print("Transformer loop quitting")

def signal_transformer_stop(e=None,wtf=None, ever=None):
    global stopRequested
    stopRequested = True


def transform(r):

    # print("Transformer working")   
    # Retrieve source image
    sourceFileName = f"user_data/{r.user}/{r.imagename}"

    pre, _ = os.path.splitext(r.imagename)
    pngFilename = f"{pre}.png"   
    destFileName = f"user_data/{r.user}/{r.style}_{pngFilename}"
    print("Transformer working on:", destFileName)
    threadLocalRecord = user_data.query.filter(user_data.uuid==r.uuid).first()    
    f = BytesIO()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    objs = list(bucket.objects.filter(Prefix=sourceFileName))
    if len(objs) > 0 and objs[0].key == sourceFileName:
        bucket.download_fileobj(sourceFileName, f)
        
        # Stylize
        outFile = BytesIO()
        try:
            stylize(f, outFile, os.path.join(STATIC_DIRECTORY, "offeredStyles", f"{r.style}.pth"))
            threadLocalRecord.producturi = f"http://s3.us-east-1.amazonaws.com/{BUCKET_NAME}/{destFileName}"
        except:
            threadLocalRecord.producturi = "Unreadable"
        # Save Product
        if outFile.getbuffer().nbytes > 0:
            bucket.put_object(Key=destFileName, Body=outFile.getvalue())
    else:
        threadLocalRecord.producturi = "File failed to save"

    # Update Product item
    db.session.commit()

@application.errorhandler(404)
def page_not_found(error):
    uid = request.cookies.get('uid')
    return render_template('page_not_found.html', uid=uid), 404

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

# atexit.register(signal_transformer_stop)
# import signal
# signal.signal(signal.SIGINT, signal_transformer_stop)
# signal.signal(signal.SIGTERM, signal_transformer_stop)
processQueue = KaraokeQueue([], lambda x:x.user)

BUCKET_NAME = 'seng6285-project'

stopRequested = False

# Stop checked boolean for transformer

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
if len(os.listdir(os.path.join(STATIC_DIRECTORY,"offeredStyles"))) == 0:
    downloadDirectoryFromS3(BUCKET_NAME, 'offeredStyles')


transformerThread = threading.Thread(target=run_transformer)
transformerThread.daemon = True
transformerThread.start()
if __name__ == '__main__':
    application.run(debug=True, use_reloader=True)
#    application.run(host='0.0.0.0')
