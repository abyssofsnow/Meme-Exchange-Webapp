from flask import Flask, render_template
app = Flask(__name__)

	
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
	return "Login Page"

@app.route('/user/<username>')
def navigate_user_page():
	return "User Page"

@app.route('/meme/<meme_id>')
def navigate_meme_page():
	return "Meme Page"


if __name__ == '__main__':
	app.run()

