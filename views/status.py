import os
from create_app import app
from flask import Blueprint,request, render_template


status = Blueprint("status", __name__)


@status.route('/')
def check_status(blog=None):
	blog_name = blog or request.args.get('blog_name')
	
	basedir = os.path.sep.join(app.instance_path.split(os.path.sep)[:-1])
	scraper_dir = os.path.join(basedir, 'scrapers', blog_name, 'blog_extracter')
	status = "not running"
	if os.path.exists(os.path.join(scraper_dir, 'running')):
		status = "running"
	if blog:
		return status
	return render_template('executing_blog.html', blog = blog_name, status = status)

def get_last_scraped_date(blog_path):
	for fname in os.listdir(blog_path):
	    if fname.endswith('.last_scraped'):
	    	return fname.rstrip('.last_scraped')
	return 'N/A'
