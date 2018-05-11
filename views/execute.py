import os
import subprocess
from create_app import app
from flask import Blueprint,render_template,request, session

execute = Blueprint("execute", __name__)

@execute.route('/')
def start_scraping():
	blog_name = request.args.get('blog_name')
	
	basedir = os.path.sep.join(app.instance_path.split(os.path.sep)[:-1])
	scraper_dir = os.path.join(basedir, 'scrapers', blog_name, 'blog_extracter')
	"""
	run scraper only if it's not currently running
	also, 
	create a file 'running' to signify the current process is in progress
	"""
	if os.path.exists(os.path.join(scraper_dir, 'running')):
		return render_template('executing_blog.html', blog = blog_name, status = 'running')
	
	with open(os.path.join(scraper_dir, 'running'), 'w') as f:
		os.chdir(scraper_dir)	
		args = ['scrapy', 'crawl', 'blog_extract_spider']
		p = subprocess.Popen(args)
	return render_template('executing_blog.html', blog = blog_name, status = 'running')
