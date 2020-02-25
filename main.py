from flask import Flask, render_template, request
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token


app = Flask(__name__)
datastore_client = datastore.Client()

# new user creation from login page
@app.route('/createuser/<newUser>', methods=['POST'])
def createuser(newUser):
    entity = datastore.Entity(key=datastore_client.key('User'))
    entity.update({
        'username': newUser
    })
    datastore_client.put(entity)

# The home page handler
@app.route('/')
def navigate_home():
    return "Homepage"

# The login/registration page handler
@app.route('/login')
def navigate_login():
    return "Login Page"


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

        render_template('profile.html', user_to_display=user_objects[0], memes_owned=memes, own_profile=True) #For now, it will always act like it's the user's own profile.
    else:
        return "User not found"


@app.route('/user/<username>', methods=['POST'])
def update_user_page(username):
    return ""


@app.route('/sendFriendRequest', methods=['POST'])
def send_friend_request(username):
    sender = request.form['sender']
    receiver = request.form['receiver']


@app.route('meme/<meme_id>', methods=['GET'])
def navigate_meme_page(meme_id):
    # Load the datastore object for the meme.
    query = datastore_client.query(kind='Meme')
    query.add_filter('key', '=', meme_id)
    memes = list(query.fetch())

    if(len(memes) > 0):
        render_template('meme.html', meme_to_display=memes[0])
    else:
        return "Meme not found"


if __name__ == '__main__':
    app.run()

