#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth

class WikiTalker:
    """Class to connect to a password-protected xwiki page using the api."""
    def __init__(self, username="", password="", baseurl = "https://amnesty.cloud.xwiki.com"):
        self.baseurl = baseurl
        self.auth = None
        if username and password:
            self.create_handler(username, password)
        self.querystore = {}
        
    def create_handler(self, username, password):
        self.auth = HTTPBasicAuth(username, password)
        
    def get_resturl(self):
        return self.baseurl +"/xwiki/rest/"

    def get_response(self, fullstring = "", querystring="", asjson = True):
        """Sends query-string to wikipage, returns result as dictionary from json format."""
        query = ""
        if fullstring:
            query = fullstring
        elif querystring:
            query = self.get_resturl()+querystring
        else:
            query = self.get_resturl()

        if asjson:
            resp = requests.get(query+"?media=json", auth = self.auth)
            return resp.json()
        else:
            resp = requests.get(query, auth = self.auth)
            return resp
        
    def get_apppages(self, appname = "", wiki = "xwiki", excludepage = []):
        """Gets all entries of an App directly stored in the app space"""
        applist = []
        allspaces = self.get_response(querystring = "wikis/"+wiki+"/spaces/")
        for entry in allspaces["spaces"]:
            if type(entry["home"]) is str:
                if entry["home"].find(appname+".")>0:
                    for link in entry["links"]:
                        takeit = True
                        if link["rel"] != 'http://www.xwiki.org/rel/home':
                            takeit = False
                        if link["href"].find("/Code/")>0:
                            takeit = False
                        if link["href"].find("/"+appname+"/pages/WebHome") >0:
                            takeit = False
                        for page in excludepage:
                            if link["href"].find("/"+page+"/") >0:
                                takeit = False
                        if takeit: 
                            applist.append(link["href"])
        allpages = self.get_response(querystring = "wikis/"+wiki+"/spaces/"+appname+"/pages")
        for entry in allpages["pageSummaries"]:
            for link in entry["links"]:
                if link["rel"] == 'http://www.xwiki.org/rel/page':
                    if link["href"].find("/pages/Web") < 0:
                        applist.append(link["href"])
        self.querystore.setdefault(appname+"_list", applist)
        
    def get_appentries(self, appname, wiki="xwiki", limit = -1):
        """Get all direct entries of a custonm app and according values"""
        if not appname+"_list" in self.querystore:
            self.get_apppages(appname, wiki)
        objlist = {}
        if limit>0:
            counter = 0
        for url in self.querystore[appname+"_list"]:
            objlist.setdefault(url, self.get_appobject(url, appname))
            if limit > 0:
                counter += 1
                if counter > limit:
                    break
        self.querystore.setdefault(appname+"_entries", objlist)
        
    def get_appobject(self, queryurl, appname):
        """Get object info as dictionary"""
        appinfo = talker.get_response(queryurl+"/objects/"+appname+".Code."+appname+"Class/0/properties")
        propdict = {}
        if "properties" in appinfo:
            for entry in appinfo["properties"]:
                propdict.setdefault(entry["name"], entry["value"])
        return propdict
    
    def create_page(self, parenturl, pagename, pagecontent=""):
        """Add page with a given name under a parent page"""
        if parenturl[len(parenturl)-6:len(parenturl)].find("pages") < 0:
            if parenturl[len(parenturl)-1] != "/":
                parenturl += "/"
            parenturl += "pages/"
        if parenturl.find("https")<0:
            parenturl = self.baseurl+"/xwiki/rest/"+parenturl
        pageparams = {"title": pagename, "syntax": "xwiki/2.0", "content": pagecontent}
        resp = requests.put(parenturl+pagename, data=pageparams, auth=self.auth)
        if resp.ok:
            return parenturl+pagename
        else:
            return False
        
    def add_object(self, parenturl, objectclass, objectname="", attributes = {}, update=True):
        if parenturl[len(parenturl)-1]!="/":
            parenturl += "/"
        oldobjects = self.get_response(parenturl + "objects")
        fullurl = ""
        if update:
            for entry in oldobjects['objectSummaries']:
                for link in entry["links"]:
                    if link["href"].find(objectclass)>0 and not objectname:
                        fullurl = link["href"]
                    elif link["href"].find(objectname)>0:
                        if objectname.find(objectclass)<0:
                            objectname = objectname + "/" + objectname
                        fullurl = link["href"]
        if not fullurl:
            postobjurl = parenturl + "objects"
            if not "." in objectclass:
                objectclass = objectclass + ".Code." + objectclass +"Class"
            resp = requests.post(postobjurl, json = {"className": objectclass}, auth=self.auth)
            if resp.ok:
                fullurl = resp.headers["Location"]
        if not fullurl:
            print ("Did not manage to find or create object "+objectname)

        objparams = {}
        for key in attributes:
            if key.find("property#")<0:
                objparams.setdefault("property#"+key, attributes[key])
            else:
                objparams.setdefault(key, attributes[key])
        resp = requests.put(fullurl.rstrip("properties"), data = objparams, auth=self.auth)
        
    def add_attachment(self, filename, parenturl, filepath = "", filepostname = ""):
        if filename.find("http")<0:
            putfile = open(filepath+filename, 'rb')
        if not filepostname:
            filepostname = filename
        puturl = parenturl+ "/attachments/"+filepostname
        requests.put(puturl, data=putfile, auth=self.auth)
        