from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
import json
import os.path
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = b"g\xfe\xd4\xac\x19U\xc7\x14\xa89\x89/'F\xd5a"

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'user_files')

@app.route('/')
def home():
    uid = request.cookies.get('userID')
    secret = request.cookies.get('secret')
    if uid == None:
        uid = "unset"

    return render_template('home.html', codes=session.keys(), uid=uid)

@app.route('/your-url', methods=['GET', 'POST'])
def your_url():
    if request.method == 'POST':
        urls = {}

        if os.path.exists('urls.json'):
            with open('urls.json', 'r') as url_file:
                urls = json.load(url_file)

        if request.form['code'] in urls.keys():
            flash('That short name has already been taken.  Please select another name.')
            return redirect(url_for('home'))

        if 'url' in request.form.keys():
            urls[request.form['code']] = {'url': request.form['url']}
        else:
            f = request.files['file']
            full_name = request.form['code'] + secure_filename(f.filename)
            f.save(os.path.join(STATIC_DIRECTORY, full_name))
            urls[request.form['code']] = {'file': full_name}

        with open('urls.json', 'w') as url_file:
            json.dump(urls, url_file)
            session[request.form['code']] = True

        return render_template("your_url.html", code=request.form['code'] )
    if request.method == 'GET':
        return redirect(url_for('home'))

@app.route("/<string:code>")
def redirect_to_url(code):
    if os.path.exists('urls.json'):
        with open('urls.json', 'r') as url_file:
            urls = json.load(url_file)
        if code in urls.keys():
            if 'url' in urls[code].keys():
                return redirect(urls[code]['url'])
            else:
                return redirect(url_for('static', filename='user_files/'+urls[code]['file']))
    return abort(404)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


@app.route("/api")
def session_api():
    return jsonify(list(session.keys()))