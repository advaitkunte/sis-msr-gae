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

import results
import sis

start_html = """
    <html>
            <title> Alpha MSRIT SIS 9</title>
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
    <h2>Testing new SIS please have patience</h2>
    <h1>Android App<br>
    <a href="https://play.google.com/store/apps/details?id=com.sismsr"><img src="http://www.blog.catblogosphere.com/cb-content/uploads/2013/07/google_play_icon.png" alt="SIS MSR Android App"></a></h1>
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
        <ul><h3>version - 9</h3>
            <li><a href = "/sis">Testing new SIS</a></li>
        </ul>
        <ul><h3>version - 8</h3>
            <li>Removed SIS (manvish)</li>
            <li><a href = "/result">added MSRIT results in json format</a></li>
        </ul>
    </p>
"""

credits_html = """
    <p><h3>Credits</h3>
        <ul>
            <li>Adarsh J (New SIS login) <i>P.S. Thank you hackmaster ;)</i> </li>
            <li>Abhigna N (Backend) <a href="https://github.com/abhigna/scraper-sis">scraper-sis Github</a> </li>
            <li>Anil M (Crawler) </li>
            <li>Dwarakesh (Windows Phone App, Backend) </li>
            <li>Advait (Android App, Backend, Crawler) </li>
        </ul>
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

sis_html = """
    <form action = "/sis" method = "post">
        <label for = "usn"> USN: </label>
        <input name = "usn" type = "text" autofocus><br>

        <label for = "password"> Password: </label>
        <input name = "password" type = "password"><br>
        
        <input type = "submit" value = "Submit"><br>
    </form>
"""

sis_login_html = """
    <form action = "/login" method = "post">
        <label for = "usn"> USN: </label>
        <input name = "usn" type = "text" autofocus><br>

        <label for = "password"> Password: </label>
        <input name = "password" type = "password"><br>
        
        <input type = "submit" value = "Submit"><br>
    </form>
"""

sis_cookie_html = """
    <form action = "/cookie" method = "post">
        <label for = "cookie"> Cookie: </label>
        <input name = "cookie" type = "text" autofocus><br>
        
        <input type = "submit" value = "Submit"><br>
    </form>
"""

class MainHtml(webapp2.RequestHandler):

    def get(self):
        self.response.out.write(start_html+main_html+changelog_html+bugs_html+credits_html+end_html)

    def post(self):
        self.response.out.write(start_html+maintenance+d+changelog_html+bugs_html+credits_html+end_html)

class ResultMSRIT(webapp2.RequestHandler):

    def get(self):
        self.response.out.write(start_html+results_html+end_html)

    def post(self):
        result_type = self.request.get("type")
        usn = self.request.get("usn")
        usn = usn.upper()
        usn = usn.replace(" ", "")
        # usn_valid = re.compile("(^1MS\d{2}\w{2,3}\d{2,3}$)")
        usn_valid = re.compile("(^1M[S|Y]\d{2}\w{2,3}\d{2,3}$)")
        logging.info("USN: " + str(usn))
        self.response.headers['Content-Type'] = 'application/json'
        if(re.search(usn_valid,usn)):
            pass
        else:
            log = "Invalid USN"
            logging.warning(log)
            # code Invalid USN
            code = {"code" : 2, "desc" : "Invalid USN\nContact advait [at] msrit {dot} edu if your USN is correct"}
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(code))
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

        try:
            rdata = urlfetch.fetch( url = url, 
                                    follow_redirects = False, 
                                    deadline = 30)
        except Exception as e:
            log = "HTTP error"
            logging.warning(log)
            log = traceback.format_exc()
            logging.warning(log)
            # code HTTP error
            code = {"code" : 1, "desc":"HTTP error - " + str(e)}
            self.response.out.write(json.dumps(code))
            return


        if rdata.status_code == 200:
            d = results.MSRITResult()
            logging.info("HTTP returned success")

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

            self.response.out.write(json.dumps(final_json))

        else:
            log = "HTTP warning"
            logging.error(log + "\tStatus code : " + rdata.status_code)
            status_code = rdata.status_code
            code = {"code" : status_code, "desc":"HTTP Error ("+str(status_code)+")"}
            self.response.out.write(json.dumps(code))

class SISMSRIT(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(start_html+sis_html+end_html)

    def post(self):
        usn = self.request.get("usn")
        usn = usn.upper()
        usn = usn.replace(" ", "")
        password = self.request.get("password")
        
        # usn_valid = re.compile("(^1M[S|Y]\d{2}\w{2,3}\d{2,3}$)")
        usn_valid = re.compile("(^1MS\d{2}\w{2}\d{3}$)")
        logging.info("USN: " + str(usn))
        self.response.headers['Content-Type'] = 'application/json'
        if(re.search(usn_valid,usn)):
            pass
        else:
            log = "Invalid USN"
            logging.warning(log)
            # code Invalid USN
            code = {"status" : 2, "desc" : "Invalid USN\nOnly support Engg USN for now\nContact advait [at] msrit {dot} edu if your USN is correct"}
            final_json = json.dumps(code)
            self.response.out.write(final_json)
            return

        d = sis.MSRITSIS()
        d.init(usn,password)
        d.result['status'] = d.status
        d.result['desc'] = d.desc
        self.response.out.write(json.dumps(d.result))
        del d

class SISMSRITLogin(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(start_html+sis_login_html+end_html)

    def post(self):
        usn = self.request.get("usn")
        usn = usn.upper()
        usn = usn.replace(" ", "")
        password = self.request.get("password")
        
        # usn_valid = re.compile("(^1M[S|Y]\d{2}\w{2,3}\d{2,3}$)")
        usn_valid = re.compile("(^1MS\d{2}\w{2}\d{3}$)")
        logging.info("USN: " + str(usn))
        self.response.headers['Content-Type'] = 'application/json'
        if(re.search(usn_valid,usn)):
            pass
        else:
            log = "Invalid USN"
            logging.warning(log)
            # code Invalid USN
            code = {"status" : 2, "desc" : "Invalid USN\nOnly support Engg USN for now\nContact advait [at] msrit {dot} edu if your USN is correct"}
            final_json = json.dumps(code)
            self.response.out.write(final_json)
            return

        d = sis.MSRITSIS()
        d.login(usn,password)
        if(d.status == 200):
            self.response.out.write(json.dumps({'cookie':d.headers['Cookie']}))
        else:
            self.response.out.write(json.dumps({'status':d.status,'desc':d.desc}))

class SISMSRITCookie(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(start_html+sis_cookie_html+end_html)

    def post(self):
        cookie = self.request.get("cookie")
        logging.info("Cookie: " + str(cookie))
        self.response.headers['Content-Type'] = 'application/json'
        
        d = sis.MSRITSIS()
        d.get_data(cookie)
        if(d.status == 200):
            self.response.out.write(json.dumps(d.result))
        else:
            self.response.out.write(json.dumps({'status':d.status,'desc':d.desc}))

app = webapp2.WSGIApplication([('/', MainHtml),('/result', ResultMSRIT),('/sis', SISMSRIT),('/login', SISMSRITLogin),('/cookie', SISMSRITCookie)], debug = True)
