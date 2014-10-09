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

key_string = ""


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
            final_json = json.dumps(code)
            self.response.out.write(final_json)
            return


        if rdata.status_code == 200:
            d = MSRITResult()
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

            self.response.out.write(final_json)

        else:
            log = "HTTP warning"
            logging.error(log + "\tStatus code : " + rdata.status_code)
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
                log = "No result or invalid USN"
                logging.info(log)
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
                    log = "Error at finding subject details at main result"
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
                    log = "Error at finding subject details at main/makeup reval"
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
                        data["grade"] = col[3].string.strip()
                    else:
                        data["grade"] = ""

                    subs.append(data)
                except Exception as e:
                    log = "Error at finding subject details at Makeup"
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
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(final_json)
            return

        d = MSRITSIS()
        d.init(usn,password)
        d.result['status'] = d.status
        d.result['desc'] = d.desc
        self.response.out.write(json.dumps(d.result))

class MSRITSIS():

    status = 0
    desc = 'Unknown error'
    subs = []
    result = {'sis':subs,'tt':subs}

    def init(self,username,password):
        import random
        import math
        import urllib
        import urllib2
        import base64,cookielib

        url = 'http://parents.msrit.edu/index.php'
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36'
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        try:
            # to get first cookie and other parameters
            # response = opener.open(url)
            headers =   {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent' : user_agent
                        }
            response = urlfetch.fetch(  url = url, 
                                        follow_redirects = False, 
                                        headers= headers,
                                        deadline = 10)

            cookie = response.headers.get('set-cookie')

            if 'We are currently performing maintenance' in response.content:
                self.status = 110
                self.desc = 'SIS site under maintainance'
                return

            token = []
            val = ''
            bs = BeautifulSoup(response.content)
            table = bs.find("table").find('tr').findAll('input')

            val = table[len(table)-3].get('value')
            token.append(table[len(table)-1].get('name'))
            token.append(table[len(table)-1].get('value'))

            def anotherfunction():
                n = math.floor(random.random()*62)
                n = int(n)
                if(n<10):
                    return n
                if(n<36):
                    return chr(n+55)
                return chr(n+61)

            def randomstring(L):
                s = ''
                while(len(s)<L):
                    s += str(anotherfunction())
                return s

            randsting = ''
            for i in range(0,len(password)):
                randsting += password[i]+randomstring(2)

            # getting encoded password
            encoded = base64.standard_b64encode(randsting)

            # building the POST param
            values = {
                      'username' : username,
                      'password' : encoded,
                      'passwd' : encoded,
                      'option' : 'com_user',
                      'task' : 'login',
                      'remember' : 'No',
                      'return' : val,
                      'return' : '',
                      token[0] : token[1]
                      }
            data = urllib.urlencode(values)
            # getting login cookie
            # response = opener.open(url, data)
            headers['Cookie'] = cookie
            response = urlfetch.fetch(  url = url, 
                                        payload = data, 
                                        method = urlfetch.POST,
                                        follow_redirects = False, 
                                        headers= headers,
                                        deadline = 10)
            headers['Cookie'] = response.headers.get('set-cookie')
            url = response.headers.get('location')
            response = urlfetch.fetch(  url = url,
                                        follow_redirects = False, 
                                        headers= headers,
                                        deadline = 10)

            if url == 'http://parents.msrit.edu/index.php':
                self.status = 1
                self.desc = 'Invalid Username / Password'
                return

            self.status = 200
            self.desc = 'success'
            self.process_data(response.content)

        except Exception as e:
            self.status = 100
            self.desc = 'Connection to SIS error\n' + str(e)
            logging.warning(str(e))
            log = traceback.format_exc()
            logging.warning(log)

    def process_data(self,html_source):
        # for today's timetable
        def timetable(row):
            subs = []
            try: 
                date = row[1].string.replace('Timetable','').strip()
                if not str(row[2]).find('No Classes Scheduled today!') > 0:
                    for timetable in row[2].findAll('li'):
                        data = {}
                        data['name'] = timetable.find('div',{'class':'first'}).string.strip()
                        x = timetable.find('div',{'class':'second'}).findAll('div',{'class':'right-bottom'})
                        data['room'] = x[1].string.strip()
                        xx = timetable.find('div',{'class':'left'}).findAll('td')
                        data['time'] = xx[0].string
                        data['code'] = xx[1].string
                        data['duration'] = xx[2].string
                        xy = x[0].string.strip().split('-')
                        data['semester'] = xy[0].replace('Semester','').strip()
                        data['section'] = xy[1].replace('Section','').strip()
                        subs.append(data)
            except Exception as e:
                log = str(e)
                logging.error(log)
                self.desc = 'Parsing error for timetable'
                self.status = 2
            return subs

        def details(table):
            subs = []
            for tab in table.findAll('div',{'class':'big_container'}):
                data = {}
                basic = tab.find('table').findAll('td')
                
                # basic
                data['sub_code'] = basic[0].string.strip()
                data['sub_name'] = basic[1].string.strip()
                
                # 
                attendance = tab.find('div',{'class':'boxmiddle'}).findAll('tr')
                marks = tab.find('div',{'class':'boxright'}).findAll('tr')
                details = tab.find('div',{'class':'boxleft'}).findAll('tr')
                
                # attendance
                data['percentage'] = attendance[2].string.strip()
                if attendance[4].findAll('span')[0].string:
                    data['attended'] = int(attendance[4].findAll('span')[0].string)
                else:
                    data['attended'] = 0
                
                if attendance[4].findAll('span')[1].string:
                    data['conducted'] = int(attendance[4].findAll('span')[1].string)
                else:
                    data['conducted'] = 0
                
                # details
                data['credits'] = details[4].string.strip()
                data['type'] = details[6].string.strip()
                data['nature'] = details[8].string.strip()
                data['cie_max'] = float("%0.2f" % float(details[10].string.strip()))
                data['see_max'] = float("%0.2f" % float(details[12].string.strip()))


                # CIE marks
                if len(marks) < 3:
                    data['T1'] = float("%0.2f" % float(-1))
                    data['T2'] = float("%0.2f" % float(-1))
                    data['T3'] = float("%0.2f" % float(-1))
                else:
                    # TODO 
                    pass
                subs.append(data)
            return subs

        try:
            bs = BeautifulSoup(html_source)
            table = bs.find("td",{'width':'60%','style':'vertical-align:top;padding:0px 5px 0px 5px;border-right:1px dashed black'})
            # table = bs.find('div',{'id':'left-column'}).find('table',{'width':'980px'}).findAll('tr')[2].find('td',{'style':'vertical-align:top;padding:0px 5px 0px 5px;border-right:1px dashed black'})
            row = table.findAll('tr')
            self.result['tt'] = timetable(row)
            # self.result['sis'] = details(table)
        except Exception, e:
            self.status = 101
            self.desc = 'Parse error'
            logging.warning(str(e))
            log = traceback.format_exc()
            logging.warning(log)
        

app = webapp2.WSGIApplication([('/', MainHtml),('/result', ResultMSRIT),('/sis', SISMSRIT)], debug = True)
