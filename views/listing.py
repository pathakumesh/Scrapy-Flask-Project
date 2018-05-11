import csv
import os
from flask import Blueprint,render_template, session,request
from create_app import app
from etc.blog_urls import blog_urls
from status import check_status, get_last_scraped_date

listing = Blueprint("listing", __name__)

basedir = os.path.sep.join(app.instance_path.split(os.path.sep)[:-1])
BASE_DIR = os.path.join(basedir, 'scrapers')

@listing.route('/')
def list_blogs():	
	basedir = os.path.sep.join(app.instance_path.split(os.path.sep)[:-1])
	scraper_dir = os.path.join(basedir, 'scrapers')
	blogs = [_dir for _dir in os.listdir(scraper_dir) if os.path.isdir(os.path.join(scraper_dir, _dir))]
	prepared_data = list()
	for blog in blogs:
		_status = check_status(blog)
		last_scraped_date = get_last_scraped_date(os.path.join(scraper_dir, blog, 'blog_extracter'))
		prepared_data.append({
				'blog_name': blog,
				'blog_url': blog_urls.get(blog),
				'scrape_status': _status,
				'last_scraped_date': last_scraped_date
			})
	return render_template('display_blogs.html', blogs=prepared_data)

@listing.route('/get_scraped_data')
def get_scraped_data():
	blog_name = request.args.get('blog_name')
	data = list()
	scraped_data_file = os.path.join(BASE_DIR, blog_name, 'blog_extracter', 'scraped_output.csv')
	if os.path.exists(scraped_data_file):
		with open(scraped_data_file, 'r') as csv_file:
			rows = list(csv.reader(csv_file))[1:]
			for row in rows:
				data.append({
					'title':row[0],
					'link':row[1],
					'word_count':row[2],
					'date':row[3],
					'author':row[4],
					'comments_count':row[5],
				})

	return render_template('display_scraped_data.html', data=data, blog=blog_name)

