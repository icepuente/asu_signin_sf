### Author: Alec Puente
### Email: icepuente@gmail.com

from flask import Flask, render_template, redirect, url_for, request, session
from sf_manager import get_sf_session, query_salesforce, add_case


# create the application object
app = Flask(__name__)
app.secret_key = "APP SECRET KEY HERE"

# use decorators to link the function to a url
@app.route('/')
def home():
	return redirect(url_for('login'))

# if post redirect to issue entry, otherwise show liability form
@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
	if request.method == 'POST':
		return redirect(url_for('issues_page'))
	# redirect to login page if no login session exists
	if session.get('email') is None:
		return redirect(url_for('login'))
	return render_template('welcome.html', username=session['username'],
		idnumber=session['idnumber'], email=session['email'])

# render issue entry page and if post from request, then add entry to SF using inputted 
# information	
@app.route('/issue', methods=['GET', 'POST'])
def issues_page():
	if session.get('email') is None:
		return redirect(url_for('login'))
	if request.method == 'POST':
		add_case(session['sf_session'], session['id'], request.form['issue'])
		return redirect(url_for('login'))
	return render_template('issue.html', username=session['username'])

# login screen, ASURITE Username and 12-digit ID number
# keeps prompting until and username and id pair match a
# contact in Salesforce
@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	username = None
	idnumber = None
	email = None
	# clear session upon calling login method each time
	session.clear()
	if request.method == 'POST':
		username = request.form['username']
		idnumber = request.form['idnumber']
		sf_session = get_sf_session()
		json_response = query_salesforce(sf_session, username,
			idnumber)

		if not json_response['records']:
			error = 'ASURITE Username and/or ID is invalid'
			return render_template('login.html', error=error)
		else:
			# save session to carry on sign process
			session['username'] = username
			session['idnumber'] = idnumber
			session['email'] = json_response['records'][0]['Email']
			session['id'] = json_response['records'][0]['Id']
			session['sf_session'] = sf_session
			return redirect(url_for('welcome'))

	return render_template('login.html', error=error)


# start the server with the 'run()' method
if __name__ == '__main__':
	app.run(debug=True)