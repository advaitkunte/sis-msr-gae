from bs4 import BeautifulSoup
import logging
import traceback
import webapp2
import string
import re
from google.appengine.api import urlfetch
import random
import math
import urllib
import urllib2
import base64


class MSRITSIS():
    url = 'http://parents.msrit.edu/index.php'
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36'
    status = 0
    desc = 'Unknown error'
    result = {}
    headers = {}

    def __init__(self):
        self.status = 0
        self.desc = 'Unknown error'
        self.result = {}
        self.headers = {}
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['User-Agent'] = self.user_agent

    def __del__(self):
      class_name = self.__class__.__name__
      self.result = {}
      self.headers = {}

    def login(self,username,password):
        try:
            # STEP 1
            logging.info('step1: getting values and cookie')
            response = urlfetch.fetch(  url = self.url, 
                                        follow_redirects = False, 
                                        headers= self.headers,
                                        deadline = 10)

            cookie = response.headers.get('set-cookie')

            if not response.status_code == 200:
                self.status = response.status_code
                self.desc = 'HTTP Error %d to SIS server\nUnable to connect to SIS server' % (self.status)
                logging.warning(self.desc)
                logging.info(response.headers)
                return

            if 'We are currently performing maintenance' in response.content:
                self.status = 503
                self.desc = 'SIS site under maintainance'
                logging.warning(self.desc)
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
            self.headers['Cookie'] = cookie

            # STEP 2
            logging.info('step2: logging in')
            response = urlfetch.fetch(  url = self.url, 
                                        payload = data, 
                                        method = urlfetch.POST,
                                        follow_redirects = False, 
                                        headers= self.headers,
                                        deadline = 10)
            self.headers['Cookie'] = response.headers.get('set-cookie')
            self.url = response.headers.get('location')
            logging.info(self.headers['Cookie'])
            if self.url == 'http://parents.msrit.edu/index.php':
                self.status = 1
                self.desc = 'Invalid Username / Password'
                logging.info(self.desc)
                return
            else:
                self.status = 200
                self.desc = 'Success'

        except Exception as e:
            self.status = 500
            self.desc = 'Connection to SIS error\n' + str(e)
            logging.warning(str(e))
            log = traceback.format_exc()
            logging.warning(log)

    def get_data(self,cookie):
        # STEP 3
        try:
            # TODO regex cookie is valid
            url_ = 'http://parents.msrit.edu/index.php?option=com_studentdashboard&controller=studentdashboard&task=dashboard'
            logging.info('step3: getting html source')
            self.headers['Cookie'] = str(cookie)
            logging.info(self.headers)
            response = urlfetch.fetch(  url = url_,
                                        follow_redirects = False, 
                                        headers= self.headers,
                                        deadline = 10)
            self.url = response.headers.get('location')
            if not response.status_code == 200:
                self.status = response.status_code
                self.desc = 'HTTP Error %d to SIS server\nUnable to connect to SIS server' % (self.status)
                logging.warning(self.desc)
                return
            if 'You are not login' in response.content:
                self.status = 1
                self.desc = 'Invalid Cookie, Login again'
                logging.warning(self.desc)
                return

            self.status = 200
            self.desc = 'success'
            self.process_data(response.content)
        except Exception as e:
            self.status = 500
            self.desc = 'Connection to SIS error\n' + str(e)
            logging.warning(str(e))
            log = traceback.format_exc()
            logging.warning(log)


    def init(self,username,password):
        cookie = self.login(username,password)
        if(self.status==200):
            self.get_data(cookie)

    def process_data(self,html_source):
        # for today's timetable
        logging.info('step4: processing data')
        def timetable(row):
            subs = []
            date = ''
            try:
                date = table.findAll('tr')[0].findAll('td')[0].findAll('td')[0].string.replace('Timetable','').strip()
                tt_subs = table.find('ul',{'id':'accordion1'}).findAll('li')
                if str(table.findAll('tr')[2]).find('No Classes Scheduled today!') > 0:
                    data = {'subjects':subs,'date':date}
                    return data
                for sub in tt_subs:
                    sub = sub.find('div',{'class':'sliderslider'})
                    data = {}
                    data['time'] = sub.find('td',{'class':'left-top'}).string.strip()
                    data['code'] = sub.find('td',{'class':'left-middle'}).string.strip()
                    data['duration'] = sub.find('td',{'class':'left-bottom'}).string.strip()
                    data['name'] = sub.find('div',{'class':'first'}).string.strip()
                    x = sub.findAll('div',{'class':'right-bottom'})
                    data['room'] = x[1].string.strip()
                    data['semester'] = int(x[0].string.split('-')[0].replace('Semester','').strip())
                    data['section'] = x[0].string.split('-')[1].replace('Section','').strip()
                    subs.append(data)
                data = {'subjects':subs,'date':date}
                return data
            except Exception as e:
                log = str(e)
                logging.warning(log)
                self.desc = 'Parsing error for timetable'
                self.status = 2
                data = {'subjects':subs,'date':date}
                log = traceback.format_exc()
                logging.warning(log)   
                return data

        def details(table):
            subs = []
            for tab in table.findAll('div',{'class':'big_container'}):
                try:
                    data = {}
                    basic = tab.find('table').findAll('td')
                    
                    # basic
                    data['sub_code'] = basic[0].string.strip()
                    data['sub_name'] = basic[1].string.strip()
                    if basic[2].string:
                        data['batch'] = basic[2].string.strip()
                    else:
                        data['batch'] = ''
                    
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
                    cie = []
                    for x in range(0,(len(marks)-2)/4):
                        dat = {}
                        dat['name'] = marks[x+1].findAll('td')[0].string.strip()
                        dat['entered'] = marks[x+1].findAll('td')[1].string.strip().replace("Marks Entered on ","")
                        dat['max'] = float("%0.2f" % float(marks[x+3].findAll('td')[2].string.strip()))
                        dat['obtained'] = float("%0.2f" % float(marks[x+3].findAll('td')[4].string.strip()))
                        cie.append(dat)
                    data['cie'] = cie
                    subs.append(data)
                except Exception, e:
                    log = str(e)
                    logging.warning(log+'\nParsing error at details()')
                    log = traceback.format_exc()
                    logging.warning(log)
            return subs

        try:
            bs = BeautifulSoup(html_source,"lxml")
            table = bs.find("td",{'width':'60%','style':'vertical-align:top;padding:0px 5px 0px 5px;border-right:1px dashed black'})
            # table = bs.find('div',{'id':'left-column'}).find('table',{'width':'980px'}).findAll('tr')[2].find('td',{'style':'vertical-align:top;padding:0px 5px 0px 5px;border-right:1px dashed black'})
            row = table.findAll('tr')
            self.result['tt'] = timetable(row)
            self.result['sis'] = details(table)
        except Exception, e:
            self.status = 101
            self.desc = 'Parse error'
            logging.warning(str(e))
            log = traceback.format_exc()
            logging.warning(log)
        