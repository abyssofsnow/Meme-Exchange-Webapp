
from flask import Flask, Response, abort, render_template, request, jsonify
from google.auth.transport import requests
from google.cloud import datastore, storage


import google.oauth2.id_token
import json
import logging
import os
import datetime

app = Flask(__name__)
datastore_client = datastore.Client('memes-marketplace')
storage_client = storage.Client.from_service_account_json("credentials.json")

firebase_request_adapter = requests.Request()

#configuring environment variable via app.yaml
#CLOUD_STORAGE_BUCKET = os.environ['CLOUD-STORAGE-BUCKET']

# Tim's section {
# new user creation from login page
@app.route('/createuser/<newUser>/<UserName>', methods=['POST'])
def createuser(newUser, UserName):
    entity = datastore.Entity(key=datastore_client.key('User', newUser))
    entity.update({
        'username': UserName,
        'bio': '',
        'picture': '',
        'email': newUser
    })
    datastore_client.put(entity)
    return 'Create User Success!'


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/readiness_check', methods=['GET'])
def readiness_check():
    return 'OK'


@app.route('/liveness_check', methods=['GET'])
def liveness_check():
    return 'OK'


# The login/registration page handler
@app.route('/login')
def navigate_login():
    return render_template('login.html')


@app.route('/trade', methods=['GET'])
def trade():
    identity = get_identity()
    app.logger.error(identity)
    queryout = datastore_client.query(kind='Trade_Request')
    queryout.add_filter('sender', '=', identity)
    outgoing_trades = list(queryout.fetch())
    queryin = datastore_client.query(kind='Trade_Request')
    queryin.add_filter('receiver', '=', identity)
    incoming_trades = list(queryin.fetch())
    ins = ""
    for i in incoming_trades:
        ins = ins + renderintrade(i)
    outs = ""
    for i in outgoing_trades:
        outs = outs + renderouttrade(i)
    return render_template("trades.html", intrades=ins, outtrades=outs)


def renderintrade(intrade):
    output = "<tr><td>" + str(intrade['meme_offered']) + "</td><td>" + str(
        intrade['meme_requested']) + "</td><td>" + str(
        intrade['sender']) + "</td><td><button type=\"button\" onclick=\"confirmTrade(\'" + str(
        intrade['trade_id']) + "\')\">Confirm Trade</button></td>"
    return output


def renderouttrade(outtrade):
    output = "<tr><td>" + str(outtrade['meme_offered']) + "</td><td>" + str(
        outtrade['meme_requested']) + "</td><td>" + str(outtrade['receiver']) + "</td>"
    return output


@app.route('/trade/<memeid>', methods=['GET'])
def requesttrade(memeid):
    return navigate_memeselector(get_identity(), memeid)


@app.route('/trade/<requested>/<offered>')
def generateATrade(requested, offered):
    Moffered = datastore_client.query(kind='Meme')
    Moffered.add_filter('id', '=', int(offered))
    Mofferedmeme = list(Moffered.fetch())
    Mrequested = datastore_client.query(kind='Meme')
    Mrequested.add_filter('id', '=', int(requested))
    Mrequestedmeme = list(Mrequested.fetch())

    newtrade = datastore.Entity(datastore_client.key('Trade_Request'))

    newtrade.update({
        'meme_offered': offered,
        'meme_requested': requested,
        'receiver': Mrequestedmeme[0]['owner'],
        'sender': Mofferedmeme[0]['owner'],
        'trade_id': str(offered) + str(requested)
    })
    datastore_client.put(newtrade)
    return redirect(url_for('trade'))


def navigate_memeselector(username, memetotradefor):
    identity = get_identity()

    user_viewed = get_datastore_user_obj(username)

    try:
        username = user_viewed['username']

        # Get the profile picture of the profile we're showing.
        profile_picture_url = create_avatar_display_url(user_viewed['picture'])

        # Load the memes associated with the user to be displayed.
        query = datastore_client.query(kind='Meme')
        query.add_filter('owner', '=', username)
        memes = list(query.fetch())

        return render_template('selector.html', profile_picture_url=profile_picture_url, user_to_display=user_viewed,
                               safe_user_to_display=json.dumps(user_viewed), memes_owned=memes, identity=identity,
                               request=memetotradefor)
    except TypeError:
        return render_template('not_found.html', type_of_entity='User', identifier=username)


@app.route('/trade/confirm/<completeTradeID>', methods=['POST'])
def completetrade(completeTradeID):
    completeTradeQuery = datastore_client.query(kind='Trade_Request')
    completeTradeQuery.add_filter('trade_id', '=', str(completeTradeID))
    theTradeToComplete = list(completeTradeQuery.fetch())
    offered = datastore_client.query(kind='Meme')
    offered.add_filter('id', '=', int(theTradeToComplete[0]['meme_offered']))
    offeredmeme = list(offered.fetch())
    requested = datastore_client.query(kind='Meme')
    requested.add_filter('id', '=', int(theTradeToComplete[0]['meme_requested']))
    requestedmeme = list(offered.fetch())
    requestedmeme[0]['owner'] = str(theTradeToComplete[0]['receiver'])
    offeredmeme[0]['owner'] = str(theTradeToComplete[0]['sender'])
    app.logger.error(str(theTradeToComplete[0]['sender']) + 'sender')
    app.logger.error(str(requestedmeme[0]['owner'] + 'also sender'))
    app.logger.error(str(theTradeToComplete[0]['receiver']) + 'receiver')
    app.logger.error(str(offeredmeme[0]['owner'] + 'also receiver'))
    datastore_client.delete(theTradeToComplete[0].key)
    datastore_client.put(offeredmeme[0])
    datastore_client.put(requestedmeme[0])
    return redirect(url_for('trade'))


# } Tim's section end. ===================================================

# Kyle's section here { ================================================
# The home page handler
@app.route('/')
def navigate_home():
	return render_template("home.html")

@app.route('/home')
def go_home():
	return render_template("home.html")
	
@app.route('/popularMeme')
def go_popularMeme():
	return render_template("popularMeme.html")
	
@app.route('/notification')
def go_notification():
	return render_template("notificationNS.html")

@app.route('/user/<username>/notification', methods=['GET'])
def go_user_notification(username):
	return render_template("notification.html")

@app.route('/user/<username>/home', methods=['GET'])
def go_user_home(username):
	return render_template("home.html",username=username)

# } End Kyle's section ==========================================


# Beginning Emily's section ===========================================
class User:
    username = ''


# Save a new meme and return the URL where the client can store the picture.
@app.route('/meme/save-meme', methods=['PUT'])
def save_meme():
    identity = get_identity()

    if identity == '':
        abort(403)
    if not request.is_json:
        abort(404)

    filename = request.json["filename"]
    content_type = request.json["contentType"]
    title = request.json["title"]

    if not (filename and content_type):
        # One of the fields was missing in the JSON request
        abort(404)

    # Get the url where the picture will be stored.
    picture_url = create_avatar_upload_url(filename, content_type)

    # Create the meme's key.
    incomplete_key = datastore_client.key('Meme')
    key = datastore_client.allocate_ids(incomplete_key, 1)  # Johnny Johnny please give me an id.

    # Create the meme object in datastore.
    entity = datastore.Entity(key[0])
    entity.update({
        'title': title,
        'owner': identity,
        'picture_id': filename,
        'id': key[0].id
    })
    datastore_client.put(entity)

    return jsonify({"signedUrl": picture_url, "meme_id": key[0].id})


@app.route('/meme/upload-new', methods=['GET'])
def navigate_upload_meme():
    identity = get_identity()

    if (identity == ''):
        abort(404)

    return render_template('memeUpload.html', identity=identity)


@app.route('/user/<username>', methods=['GET'])
def navigate_user_page(username):
    identity = get_identity()

    user_viewed = get_datastore_user_obj(username)

    try:
        username = user_viewed['username']

        # Get the profile picture of the profile we're showing.
        profile_picture_url = create_avatar_display_url(user_viewed['picture'])

        # Load the memes associated with the user to be displayed.
        query = datastore_client.query(kind='Meme')
        query.add_filter('owner', '=', username)
        memes = list(query.fetch())

        return render_template('profile.html', profile_picture_url=profile_picture_url, user_to_display=user_viewed,
                               safe_user_to_display=json.dumps(user_viewed), memes_owned=memes, identity=identity)
    except TypeError:
        return render_template('not_found.html', type_of_entity='User', identifier=username)


@app.route('/sendFriendRequest', methods=['POST'])
def send_friend_request():
    sender = request.json['sender']
    receiver = request.json['receiver']

    # Get both the sender and receiver objects.
    sender_obj = get_datastore_user_obj(sender)
    receiver_obj = get_datastore_user_obj(receiver)

    # Return error if they are already friends.
    try:
        for friend_entry in sender_obj['friends']:
            if (friend_entry == receiver):
                return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}
    except:
        str = "Sender has no friends;proceed"

    # Return error if the receiver has already sent the sender a friend request.
    try:
        sender_friend_requests = sender_obj['friend_request_in']

        for friend_request in sender_friend_requests:
            if (friend_request == receiver):
                return json.dumps({'success': False}), 403, {'ContentType': 'application/json'}
    except:
        str = "Sender has no friend requests; proceed"

    # Add a friend request between these two.
    try:
        receiver_friend_requests = receiver_obj['friend_request_in']

        # Make sure the sender hasn't already sent a request.
        for friend_request in receiver_friend_requests:
            if (friend_request == sender):
                return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

        receiver_friend_requests.append(sender)
    except:
        receiver_friend_requests = [sender]

        # Add the sender to the receiver's pending invites
    try:
        receiver_obj['friend_request_in'] = receiver_friend_requests
        datastore_client.put(receiver_obj)
    except:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/meme/<int:meme_id>', methods=['GET'])
def navigate_meme_page(meme_id):
    key = datastore_client.key('Meme', meme_id)
    meme = datastore_client.get(key)

    user = get_identity()

    # Get meme picture from cloud store.
    picture_url = create_avatar_display_url(meme['picture_id'])

    if (meme['title'] != ''):
        return render_template('meme.html', meme_to_display=meme, identity=user, picture_url=picture_url)
    else:
        return render_template('not_found.html', type_of_entity='Meme', identifier=meme_id)


# Update the user's profile and return the URL where the client can store the picture.
@app.route('/profile-edit/edit-with-picture', methods=['PUT'])
def edit_profile_without_picture():
    user = get_identity()

    if user == '':
        abort(403)
    if not request.is_json:
        abort(404)
    filename = request.json["filename"]
    content_type = request.json["contentType"]
    bio = request.json["bio"]

    if not (filename and content_type):
        # One of the fields was missing in the JSON request
        abort(404)

    picture_url = create_avatar_upload_url(filename, content_type)

    # Grab the user object from datastore.
    user_obj = get_datastore_user_obj(user)

    # Update the user object.
    user_obj['bio'] = bio
    user_obj['picture'] = filename
    datastore_client.put(user_obj)

    return jsonify({"signedUrl": picture_url})


# Update the user's profile and return the URL where the client can store the picture.
@app.route('/profile-edit/edit', methods=['PUT'])
def edit_profile_picture():
    user = get_identity()
    if user == '':
        abort(403)
    if not request.is_json:
        abort(404)

    bio = request.json["bio"]

    # Grab the user object from datastore.
    user_obj = get_datastore_user_obj(user)

    # Update the user object.
    user_obj['bio'] = bio
    datastore_client.put(user_obj)

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def create_avatar_upload_url(image_name, content_type):
    bucket = storage_client.bucket("memes-marketplace.appspot.com")
    blob = bucket.blob(image_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=datetime.timedelta(minutes=15),
        # Allow PUT requests using this URL
        method="PUT",
        content_type=content_type,
    )
    return url


def create_avatar_display_url(image_name):
    bucket = storage_client.bucket("memes-marketplace.appspot.com")
    blob = bucket.blob(image_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=datetime.timedelta(minutes=15),
        # Allow GET requests using this URL
        method="GET",
        # Note that when content type information is encoded in the blob
        content_type=blob.content_type,
    )
    return url


# Get the user's identity. Return the username if the user is logged in, otherwise return ''.
def get_identity():
    id_token = request.cookies.get("token")

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            # Load the datastore object for the user visiting the page.
            key = datastore_client.key('User', claims['email'])
            user_self = datastore_client.get(key)

            # If the page visitor is logged in, return  their identity.
            if (user_self is not None):
                return user_self['username']
            else:
                return ''
        except ValueError as exc:
            error_message = str(exc)

    return ''


# Get the user object, given the username.
def get_datastore_user_obj(username):
    # Query for the user whose profile we're looking for.
    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', username)
    user_viewed_list = list(query.fetch())

    # If the user is found, return its object.
    if (len(user_viewed_list) > 0):
        id_rec = user_viewed_list[0]['email']
        key = datastore_client.key('User', id_rec)
        task = datastore_client.get(key)
        return task
    else:
        user_obj = User()
        return user_obj


# } End Emily's Section ================================================


# Beginning of Jingjing's section { =================================================
@app.route('/uploadImage', methods=['POST'])
def upload(image):
    # processing and uploading image to GCS
    uploadedImg = request.files.get('file')

    if not uploadedImg:
        return 'Upload unsuccessful', 400

    # creating cloud storage client
    client = storage.Client()

    # getting bucket to upload to, environment declared in app.yaml
    bucket2load = client.get_bucket('{CLOUD_STORAGE_BUCKET}/Users/{username}')

    # creating new blob and uploading image
    link = "/Users/" + username
    blob = bucket2load.blob(uploadedImg.filename)

    # upload from file link from profile.html ex:'D:/Download/.pdf'
    blob.uploaded_from_string(data=uploadedImg, content_type='image/*', client=client)

    # profile pic can now be accessed via HTTP
    return blob.public_url


# } End Jingjing's section =====================================

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error has occurred')
    return """
	An internal error has occurred: <pre>{}</pre>
	""".format(e), 500


if __name__ == '__main__':
    app.run()




