from bs4 import BeautifulSoup
import logging
import traceback
import webapp2
import string
import re

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
            return code
        
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
                return code
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
            return code

        details = {"name":name,"usn":usn,"sem":sem,"year":year}

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
            
        desc = "success"

        # output as JSON
        if(result_type == "1"):
            out_json = {"gpa":gpa,"details":details,"subjects":subs,"code":200,"desc":desc}
        else:
            out_json = {"details":details,"subjects":subs,"code":200,"desc":desc}

        return out_json