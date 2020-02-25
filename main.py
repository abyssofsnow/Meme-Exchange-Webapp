	from flask import Flask, Response, render_template, request
	from google.cloud import datastore


	app = Flask(__name__)
	datastore_client = datastore.Client()
	

	# The home page handler
	@app.route('/')
	def navigate_home():
		return "Homepage"
	
	# The login/registration page handler
	@app.route('/login')
	def navigate_login():
		return "Login Page"

	@app.route('/user/<username>', methods = ['GET'])
	def navigate_user_page(username):

		#Load the datastore object for the user to present.
		query = datastore_client.query(kind='User')
		query.add_filter('username', '=', username)
		user_objects = list(query.fetch())

		#If the user is found, use its data to populate the profile.
		if(len(user_object) > 0)

			#Load the memes associated with this user. 
			query = datastore_client.query(kind='Meme')
			query.add_filter('owner', '=', username)
			memes = list(query.fetch())
			
			render_template('profile.html', user_to_display=user_objects[0], memes_owned=memes, own_profile=True) #For now, it will always act like it's the user's own profile.
		else
			return "User not found"

	@app.route('/user/<username>', methods = ['POST'])
	def update_user_page(username):

	@app.route('/sendFriendRequest', methods = ['POST'])
	def navigate_user_page(username):
		sender = request.form['sender']
		receiver = request.form['receiver']


	@app.route('meme/<meme_id>', methods = ['GET'])
	def navigate_meme_page(meme_id):
		#Load the datastore object for the meme.
		query = datastore_client.query(kind='Meme')
		query.add_filter('key', '=', meme_id)
		memes = list(query.fetch())

		if(len(memes) > 0)
			render_template('meme.html', meme_to_display=memes[0])
		else
			return "Meme not found"


	def read_session_cookie(cookie):
		#Look up session id in session. 

		#If found, return user name string.

		#If not, "".


	if __name__ == '__main__':
		app.run()

