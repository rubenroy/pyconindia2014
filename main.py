import os
import jinja2
import secrets
import webapp2
from data import events
from apiclient.discovery import build
from google.appengine.api import urlfetch
from apiclient.http import BatchHttpRequest
from oauth2client.appengine import OAuth2Decorator


decorator = OAuth2Decorator(
	client_id=secrets.client_id,
	client_secret=secrets.client_secret,
	scope='https://www.googleapis.com/auth/calendar')
class MainHandler(webapp2.RequestHandler):

	@decorator.oauth_required
	def get(self):		
		http = decorator.http()		
		calendars = []
		page_token = None
		while True:
			calendar_list = service.calendarList().list(pageToken=page_token,minAccessRole="writer").execute(http=http)
			for entry in calendar_list['items']:
				calendars.append({
					"summary":entry['summary'],					
					"calendar_id":entry['id']
				})
			page_token = calendar_list.get('nextPageToken')
			if not page_token:
				break
		jinja_environment = jinja2.Environment(autoescape = True,
			loader = jinja2.FileSystemLoader(os.path.join(
				os.path.dirname(__file__), 'templates')))
		tpl_vars = { "calendars": calendars}
		template = jinja_environment.get_template('index.html')
		self.response.out.write(template.render(tpl_vars))

class CreateHandler(webapp2.RequestHandler):
	@decorator.oauth_required
	def post(self):
		http = decorator.http()
		calendar = {'summary': self.request.POST.get("summary")}
		created_calendar = service.calendars().insert(body=calendar).execute(http=http)
		self.redirect("/")

	def get(self):
		self.redirect("/")

class CalendarHandler(webapp2.RequestHandler):

	@decorator.oauth_required
	def post(self):
		urlfetch.set_default_fetch_deadline(60)
		http = decorator.http()	
		calendar_id = self.request.POST.get("calendar_id")
		widget = '<iframe src="https://www.google.com/calendar/embed?height=600&amp;wkst=1&amp;bgcolor=%23FFFFFF&amp;src='+calendar_id.replace("@","%40")+'&amp;color=%23B1365F&amp;ctz=Asia%2FCalcutta" style=" border-width:0 " width="800" height="600" frameborder="0" scrolling="no"></iframe>'
		batch = BatchHttpRequest()
		for event in events:
			batch.add(service.events().insert(calendarId=calendar_id, body=event))
		batch.execute(http=http)
		self.response.write("Updated calendar: <br/>\n"+widget)

	def get(self):
		self.redirect("/")

service = build('calendar', 'v3')
app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/update',CalendarHandler),
	('/create',CreateHandler),
	(decorator.callback_path, decorator.callback_handler()),
],debug=True)