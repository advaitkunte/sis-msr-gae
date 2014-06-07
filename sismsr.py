import webapp2
from google.appengine.ext import db
from google.appengine.api import namespace_manager
from google.appengine.api import urlfetch
from gaesessions import get_current_session
import time
import logging
import string
import re
import datetime
import json
import traceback
from bs4 import BeautifulSoup

start_html = """
	<html>
			<title> Alpha MSRIT SIS 8</title>
		</head>
		<body>
"""

end_html = """
		</body>
	</html>
"""

maintenance = """
<h1>WEBSITE UNDER MAINTENANCE</h1>
"""
d = """<h1>NO MORE SUPPORT FOR MANVISH SIS (ITS CRAP!)</h1>"""

main_html = """
	<style type="text/css">
		img {
			width:  300px;
			height: auto;
			}
	</style>
	<h2>Account Details v8</h2>
	<form method = "post">
		<label for = "username"> Username: </label>
		<input name = "username" type = "text" autofocus><br>

		<label for = "password"> Password: </label>
		<input name = "password" type = "password" ><br>
		
		<input name = "" type = "submit" value = "Submit">
	</form>
	<h1>Android App<br>
	<a href="https://play.google.com/store/apps/details?id=com.sismsr"><img src="http://www.blog.catblogosphere.com/cb-content/uploads/2013/07/google_play_icon.png" alt="SIS MSR Android App"></a></h1>
	<hr>
"""

register_html = """
	<h2>Register Account</h2>
	<form method = "post">
		<label for = "username"> Username: </label>
		<input name = "username" type = "text" autofocus><br>

		<label for = "password"> Password: </label>
		<input name = "password" type = "password" ><br>
		
		<input name = "" type = "submit" value = "Register">
	</form>
	<hr>
"""

bugs_html = """
	<p><h3>Bugs</h3>
		<ul>
			<li>Results only shows Main results (Reval, Make up exam not yet supported)</li>
		</ul>
	</p>
"""

changelog_html = """
	<p><h3>Change Log</h3>
		<ul><h3>version - 8</h3>
			<li>Removed SIS (manvish)</li>
			<li><a href = "/result">added MSRIT results in json format</a></li>
		</ul>
	</p>
"""

credits_html = """
	<p><h3>Credits</h3>
		-Abhigna N (Backend) <a href="https://github.com/abhigna/scraper-sis">scraper-sis Github</a> <br>
		-Anil M (Crawler) <br>
		-Dwarakesh (Windows Phone App, Backend) <br>
		-Advait (Android App, Backend, Crawler)
	</p>
"""

results_html = """
<form action = "/result" method = "post">
		<label for = "usn"> USN: </label>
		<input name = "usn" type = "text" autofocus><br>

		<input type="radio" name="type" value="1" checked='checked' autocomplete="off">Main<br>
		<input type="radio" name="type" value="2">Reval<br>
		<input type="radio" name="type" value="3">Makeup<br>
		<input type="radio" name="type" value="4">Makeup Reval<br>
		
		<input name = "" type = "submit" value = "Submit"><br>
</form>
"""

key_string = ""

class MainHtml(webapp2.RequestHandler):

	def get(self):
		self.response.out.write(start_html+maintenance+changelog_html+bugs_html+credits_html+end_html)

	def post(self):
		self.response.out.write(start_html+maintenance+d+changelog_html+bugs_html+credits_html+end_html)

class ResultMSRIT(webapp2.RequestHandler):

	def get(self):
		self.response.out.write(start_html+results_html+end_html)

	def post(self):
		result_type = self.request.get("type")
		usn = self.request.get("usn")
		usn = usn.upper()
		usn_valid = re.compile("(^1MS\d{2}\w{2,3}\d{2,3}$)")
		logging.info("USN: " + str(usn))
		self.response.headers['Content-Type'] = 'application/json'
		if(re.search(usn_valid,usn)):
			pass
		else:
			log = "Invalid USN"
			logging.warning(log)
			# code Invalid USN
			code = {"code" : 2, "desc" : "Invalid USN"}
			final_json = json.dumps(code)
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(final_json)
			return

		if(result_type == "1"):
			url_end = "grprint.php?myusn="
		elif(result_type == "2"):
			url_end = "grvresult.php?myusn="
		elif(result_type == "3"):
			url_end = "makeup_result.php?myusn="
		elif(result_type == "4"):
			url_end = "makeup_grvresult.php?myusn="


		url = "http://result.msrit.edu/" + url_end + str(usn)
		
		logging.info("Result type = "+result_type + "\nURL "+ url)

		try:
			rdata = urlfetch.fetch( url = url, 
									follow_redirects = False, 
									deadline = 30)
		except Exception as e:
			log = "HTTP error"
			logging.error(log)
			log = traceback.format_exc()
			logging.warning(log)
			# code HTTP error
			code = {"code" : 1, "desc":"HTTP error" + str(e)}
			final_json = json.dumps(code)
			self.response.out.write(final_json)
			return


		if rdata.status_code == 200:
			d = MSRITResult()
			logging.info("Result type = "+result_type + "\nURL "+ url_end)

			if(result_type == "1"):
				logging.info("main")
				final_json = d.get_main_result(rdata.content,result_type)

			elif(result_type == "2"):
				logging.info("mainReval")
				final_json = d.get_main_result(rdata.content,result_type)

			elif(result_type == "3"):
				logging.info("makeup")
				final_json = d.get_main_result(rdata.content,result_type)

			elif(result_type == "4"):
				logging.info("makeupReval")
				final_json = d.get_main_result(rdata.content,result_type)

			self.response.out.write(final_json)

		else:
			status_code = rdata.status_code
			code = {"code" : status_code, "desc":"HTTP Error ("+str(status_code)+")"}
			final_json = json.dumps(code)
			self.response.out.write(final_json)

class MSRITResult():

	def get_main_result(self,data,result_type):
		
		num_rows = 0
		
		bs = BeautifulSoup(data)

		try:
			table = bs.find("table", {"bordercolor" : "#666666"})
			semester = bs.find("p", {"align":"center"} ).find("u").find("b").find("font").string.encode('utf-8').strip().upper()
		except Exception as e:
			log = "Didnt find table or semester"
			logging.warning(log)
			log = traceback.format_exc()
			logging.warning(log)
			# null data
			code = {"code" : 0, "desc":"No result or invalid USN"}
			final_json = json.dumps(code)
			return final_json
		
		# To find name and USN
		header = table.findAll('th')
		headers = [ th.text for th in header ]
		try:
			name = string.capwords(headers[0][7:])
			if(len(name) == 0):
				# null data
				code = {"code" : 0, "desc":"No result or invalid USN"}
				final_json = json.dumps(code)
				return final_json
			usn = headers[1][5:].upper()

			# searching for sem
			m = re.search('FOR (.+?) SEMESTER', semester)
			if m:
				sem = string.capwords(m.group(1))
			else:
				sem = ""

			# search for month and year
			if(result_type == 1 or result_type == 2):
				m = re.search('-(.*)', semester)
			else:
				m = re.search('EXAMINATIONS-(.*)', semester)
			if m:
				year = string.capwords(m.group(1))
				uniString = unicode(year, "UTF-8")
				year = uniString.replace(u"\u00A0", " ")
			else:
				year = ""

		except Exception as e:
			log = "Null name or USN, exiting"
			logging.warning(log)
			log = traceback.format_exc()
			logging.warning(log)
			# null data
			code = {"code" : 0, "desc":"No result or invalid USN"}
			final_json = json.dumps(code)
			return final_json

		details = {"name":name,"usn":usn,"sem":sem,"year":year}
		details_json = json.dumps(details)

		# To find result details
		subs = []
		for row in table.findAll('tr'):
			col = row.findAll('td')
			# Main result
			if(len(col)==5 and result_type == "1"):
				try:
					num_rows = num_rows + 1
					data = {}
					data["name"] = col[0].string.strip()
					if(col[1].string is not None):
						data["credits"] = col[1].string.strip()
					else:
						data["credits"] = ""

					if(col[2].string is not None):
						data["sub_code"] = col[2].string.strip()
					else:
						data["sub_code"] = ""

					if(col[3].string is not None):
						data["grade"] = col[3].string.strip()
					else:
						data["grade"] = ""

					if(col[4].string is not None):
						data["points"] = col[4].string.strip()
					else:
						data["points"] = ""

					subs.append(data)
				except Exception as e:
					log = "Error at finding subject details"
					logging.warning(log)
					log = traceback.format_exc()
					logging.warning(log)
			
			# Main/Makeup Reval
			elif(len(col)==4 and (result_type == "2" or result_type == "4")):
				try:
					num_rows = num_rows + 1
					data = {}
					data["name"] = col[0].string.strip()

					if(col[1].string is not None):
						data["sub_code"] = col[1].string.strip()
					else:
						data["sub_code"] = ""

					if(col[2].string is not None):
						data["old_grade"] = col[2].string.strip()
					else:
						data["old_grade"] = ""

					if(col[3].string is not None):
						data["new_grade"] = col[3].string.strip()
					else:
						data["new_grade"] = ""

					subs.append(data)
				except Exception as e:
					log = "Error at finding subject details"
					logging.warning(log)
					log = traceback.format_exc()
					logging.warning(log)
			
			# Makeup
			elif(len(col)==4 and result_type == "3"):
				try:
					num_rows = num_rows + 1
					data = {}
					data["name"] = col[0].string.strip()

					if(col[2].string is not None):
						data["sub_code"] = col[2].string.strip()
					else:
						data["sub_code"] = ""

					if(col[1].string is not None):
						data["credits"] = col[1].string.strip()
					else:
						data["credits"] = ""

					if(col[3].string is not None):
						data["new_grade"] = col[3].string.strip()
					else:
						data["new_grade"] = ""

					subs.append(data)
				except Exception as e:
					log = "Error at finding subject details"
					logging.warning(log)
					log = traceback.format_exc()
					logging.warning(log)

		
		sub_json = json.dumps(subs)

		# To find SGPA and CGPA for only Main Result
		if(result_type == "1"):
			num_rows = num_rows + 2
			rows = table.findAll('tr')
			data = []
			for tr in rows[num_rows:-1]:
				td = tr.findAll('td')
				data.append(td[0].text)
			sgpa = data[2]
			cgpa = data[5]
			gpa = {"sgpa":sgpa,"cgpa":cgpa}
			gpa_json = json.dumps(gpa)
		
			out_gpa_json = json.loads(gpa_json)

		out_details_json = json.loads(details_json)
		out_sub_json = json.loads(sub_json)
		
		desc = "success"

		# output as JSON
		if(result_type == "1"):
			out_json = {"gpa":out_gpa_json,"details":out_details_json,"subjects":out_sub_json,"code":200,"desc":desc}
		else:
			out_json = {"details":out_details_json,"subjects":out_sub_json,"code":200,"desc":desc}
		final_json = json.dumps(out_json)
		return final_json



app = webapp2.WSGIApplication([('/', MainHtml),('/result', ResultMSRIT)], debug = True)
