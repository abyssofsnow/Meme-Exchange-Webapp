from flask import Flask
app = Flask(__name__)

	
# The home page handler
@app.route('/')
def navigate_home():
	return "Home"

# The login/registration page handler
@app.route('/login')
def navigate_login():
	return "Login Page"

@app.route('/user/<username>')
def navigate_user_page():
	return "User Page"

@app.route('/meme/<meme_id>')
def navigate_meme_page():
	return "Meme Page"


if __name__ == '__main__':
	app.run()

