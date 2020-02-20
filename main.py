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

		#Load the datastore object for the user.
		query = client.query(kind='User')
		query.add_filter('username', '=', username)
		user_objects = list(query.fetch())

		#If the user is found, use its data to populate the profile.
		if(len(user_object) > 0)
			render_template('profile.html', user_to_display=user_objects[0], own_profile=True) #For now, it will always act like it's the user's own profile.
		else
			return "User not found"

	@app.route('/user/<username>', methods = ['POST'])
	def update_user_page(username):

	@app.route('/sendFriendRequest', methods = ['POST'])
	def navigate_user_page(username):
		sender = request.form['sender']
		receiver = request.form['receiver']


	@app.route('meme/<meme_id>')
	def navigate_meme_page():
		return "Meme Page"


	if __name__ == '__main__':
		app.run()

