from flask import Blueprint, render_template


frontend = Blueprint('frontend', __name__)

@frontend.route('/', methods = ['GET', 'POST'])
def index():
	return render_template('index.html')