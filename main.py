from flask import Flask, Request, render_template, request
from google.auth.transport import requests
from google.cloud import datastore
from google.cloud import storage

import google.oauth2.id_token
import json
import logging
import os


app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()

#configuring environment variable via app.yaml
CLOUD_STORAGE_BUCKET = os.environ['CLOUD-STORAGE-BUCKET']

# new user creation from login page
@app.route('/createuser/<newUser>', methods=['POST'])
def createuser(newUser):
    entity = datastore.Entity(key=datastore_client.key('User', newUser))
    entity.update({
        'username': newUser
    })
    datastore_client.put(entity)
    return render_template('login.html')

# The home page handler
@app.route('/')
def navigate_home():
    return "Homepage"

# The login/registration page handler
@app.route('/login')
def navigate_login():
    return render_template('login.html')


@app.route('/user/<username>', methods=['GET'])
def navigate_user_page(username):
    # Verify Firebase Auth.
    id_token = request.cookies.get("token")
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as exc:
            error_message = str(exc)

    # Load the datastore object for the user.
    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', username)
    user_objects = list(query.fetch())

    # If the user is found, use its data to populate the profile.
    if(len(user_objects) > 0):

        # Load the memes associated with this user. 
        query = datastore_client.query(kind='Meme')
        query.add_filter('owner', '=', username)
        memes = list(query.fetch())

		user = user_objects[0]
        return render_template('profile.html', user_to_display=user, safe_user_to_display=json.dumps(user), memes_owned=memes, own_profile=True) #For now, it will always act like it's the user's own profile.
    else:
        return "User not found"


@app.route('/user/<username>', methods=['POST'])
def update_user_page(username):
    return ""


@app.route('/sendFriendRequest', methods=['POST'])
def send_friend_request(username):
    sender = request.form['sender']
    receiver = request.form['receiver']


    # Check that this user hasn't already received a friend request from recip.
    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', sender)
    sender_objects = list(query.fetch())

    # Return error if this user already has friend request.
    for friend_request in sender_objects[0].friend_request_in:
        if(friend_request == receiver):
            return json.dumps({'success': False}), 403, {'ContentType': 'application/json'}

    # Check that this user hasn't already sent a friend request 
    # from this user.
    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', receiver)
    receiver_objects = list(query.fetch())

    # Return error if this user already sent friend request.
    for friend_request in receiver_objects[0].friend_request_in:
        if(friend_request == sender):
            return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    # Return error if they are already friends.
    for friend_request in sender_objects[0].friends:
        if(friend_request == receiver):
            return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

    # Add a friend request between these two.
    try:
        with datastore_client.transaction():
            key = datastore_client.key('User', receiver)
            task = datastore_client.get(key)

            # Add the sender to the receiver's pending invites
            task['friend_request_in'] = receiver_objects[0].friend_request_in.append(sender)

            datastore_client.put(task)
    except:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'} 

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'} 


@app.route('/uploadImage', methods=['POST'])
def upload(image):
    #processing and uploading image to GCS
    uploadedImg = request.files.get('file')

    if not uploadedImg:
        return 'Upload unsuccessful', 400

    #creating cloud storage client
    client = storage.Client()

    #getting bucket to upload to
    bucket2load = client.get_bucket(CLOUD_STORAGE_BUCKET)

    #creating blob and uploading image
    blob = bucket2load.blob(uploadedImg.filename)
    blob.uploaded_from_string(uploadedImg, content_type='image/*')

    #return updated profile pic
    return None


@app.route('/meme/<meme_id>', methods=['GET'])
def navigate_meme_page(meme_id):
    # Load the datastore object for the meme.
    query = datastore_client.query(kind='Meme')
    query.add_filter('key', '=', meme_id)
    memes = list(query.fetch())

    if(len(memes) > 0):
        render_template('meme.html', meme_to_display=memes[0])
    else:
        return "Meme not found"

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error has occurred')
    return """
    An internal error has occurred: <pre>{}</pre>
    """.format(e), 500

if __name__ == '__main__':
    app.run()

