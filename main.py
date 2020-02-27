from flask import Flask, render_template
app = Flask(__name__)
datastore_client = datastore.Client('memes-marketplace')

firebase_request_adapter = requests.Request()

#configuring environment variable via app.yaml
#CLOUD_STORAGE_BUCKET = os.environ['CLOUD-STORAGE-BUCKET']

# new user creation from login page
@app.route('/createuser/<newUser>/<UserName>', methods=['POST'])
def createuser(newUser, UserName):
    entity = datastore.Entity(key=datastore_client.key('User', newUser))
    entity.update({
        'username': UserName,
        'bio': '',
        'friend_request_in': [],
        'friends': [],
        'memes': [],
        'picture': '',
    })
    datastore_client.put(entity)
    return "Create User Success!"

	
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

# The login/registration page handler
@app.route('/login')
def navigate_login():
    return render_template('login.html')


@app.route('/user/<username>', methods=['GET'])
def navigate_user_page(username):

	identity = ''

    # Verify Firebase Auth.
    id_token = request.cookies.get("token")
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

			# Load the datastore object for the user visiting the page.
            key = datastore_client.key('User', claims['email'])
            user_self = datastore_client.get(key)

            # If the page visitor is logged in, store their identity.
            if(user_self is not None):
                identity = user_self['username']
            else:
                identity = ''
        except ValueError as exc:
            error_message = str(exc)

    # Query for the user whose profile we're looking for.
    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', username)
    user_viewed_list = list(query.fetch())

    # If the user is found, use its data to populate the profile.
    if(len(user_viewed_list) > 0):

        user_viewed = user_viewed_list[0]

        # Load the memes associated with the user to be displayed. 
        query = datastore_client.query(kind='Meme')
        query.add_filter('owner', '=', username)
        memes = list(query.fetch())

        return render_template('profile.html', user_to_display=user_viewed, safe_user_to_display=json.dumps(user_viewed), memes_owned=memes, identity=identity)
    else:
        return "User not found"


@app.route('/user/<username>', methods=['POST'])
def update_user_page(username):
    return ""


@app.route('/sendFriendRequest', methods=['POST'])
def send_friend_request():
    sender = request.json['sender']
    receiver = request.json['receiver']


    # Check that this user hasn't already received a friend request from recip.
    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', sender)
    sender_objects = list(query.fetch())

    sender_obj = sender_objects[0]
    for friend_request in sender_obj['friend_request_in']:
        if(friend_request == receiver):
            return json.dumps({'success': False}), 403, {'ContentType': 'application/json'}

    query = datastore_client.query(kind='User')
    query.add_filter('username', '=', receiver)
    receiver_objects = list(query.fetch())


    receiver_obj = receiver_objects[0]
    # Return error if this user already sent friend request.
    for friend_request in receiver_obj['friend_request_in']:
        if(friend_request == sender):
            return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    # Return error if they are already friends.
    for friend_entry in sender_obj['friends']:
        if(friend_request == receiver):
            return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

    # Add a friend request between these two.
    try:
        with datastore_client.transaction():
            key = datastore_client.key('User', receiver)
            task = datastore_client.get(key)

            # Add the sender to the receiver's pending invites
            task['friend_request_in'] = receiver_obj['friend_request_in'].append(sender)

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

@app.route('/user/<username>')
def navigate_user_page():
	return "User Page"

@app.route('/meme/<meme_id>')
def navigate_meme_page():
	return "Meme Page"


if __name__ == '__main__':
	app.run()

