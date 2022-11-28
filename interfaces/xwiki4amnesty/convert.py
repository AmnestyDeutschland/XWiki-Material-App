#!/usr/bin/env python

import pandas
import yaml

class InfoMatcher:
    def __init__(self, sourcefile = "", matchfile = "", talker = None):
        """Initializes with sourcefile of type excel and matchfile with yaml content"""
        self.source = None
        self.match = None
        self.talker = talker
        
        if matchfile != "":
            self.match = yaml.safe_load(open(matchfile, "r"))
        if sourcefile != "":
            if "formatting" in self.match:
                self.source = pandas.read_excel(sourcefile, dtype = self.match["formatting"])
            else:
                self.source = pandas.read_excel(sourcefile)
                
    def get_mapped(self, key, value, row = ""):
        mappers = {}
        outvalue = value
        if "mappers" in self.match:
            mappers = self.match["mappers"]
        if key in mappers:
            if value in mappers[key]:
                if type(mappers[key][value]) is dict:
                    if type(row) == str:
                        print ("Please pass reference entries to check conditions!")
                        return outvalue
                    for value in mappers[key]:
                        for select in mappers[key][value]:
                            cond = mappers[key][value][select]
                            for ckey in cond:
                                if row[ckey] == cond[ckey]:
                                    outvalue = select
                elif type(mappers[key][value]) is str:
                    outvalue = mappers[key][value]
        return outvalue
        
    def create_object_entries(self, updatepages = False, singleobject=False):
        for row in self.source.iterrows():
            mappers = {}
            if "mappers" in self.match:
                mappers = self.match["mappers"]
                
            objdict = {}
            pagetitle = ""

            for key in self.match["matching"].keys():
                sentry = self.match["matching"][key]
                if key == "doctitle":
                    if sentry in row[1]:
                        pagetitle = row[1][sentry]
                else:
                    if type(sentry) is str:
                        if sentry in row[1]:
                            if not pandas.isna(row[1][sentry]):
                                objdict.setdefault(key, self.get_mapped(key, row[1][sentry]))
                    elif type(sentry) is dict:
                        if "display" in sentry:
                            if sentry["display"] == "usetitle":
                                result = ""
                                for val in sentry["values"]:
                                    if val in row[1]:
                                        if not pandas.isna(row[1][val]):
                                            result += "**"+val+"**\n"+str(row[1][val])+"\n\n"
                                objdict.setdefault(key, result)
                            elif sentry["display"] == "newlines":
                                result = ""
                                for val in sentry["values"]:
                                    if val in row[1]:
                                        if not pandas.isna(row[1][val]):
                                            result += str(row[1][val])+"\n"
                                objdict.setdefault(key, result)
                            else:
                                result = ""
                                for val in sentry["values"]:
                                    if val in row[1]:
                                        if not pandas.isna(row[1][val]):
                                            result += row[1][val]
                                objdict.setdefault(key, result)
                        elif "prefix" in sentry:
                            if sentry["value"] in row[1]:
                                if not pandas.isna(row[1][sentry["value"]]):
                                    objdict.setdefault(key, sentry["prefix"]+row[1][sentry["value"]])
                        elif "suffix" in sentry:
                            if sentry["value"] in row[1]:
                                if not pandas.isna(row[1][sentry["value"]]):
                                    objdict.setdefault(key, row[1][sentry["value"]]+sentry["suffix"])
                    elif type(sentry) is list:
                        result = ""
                        for val in sentry:
                            if val in row[1]:
                                if not pandas.isna(row[1][val]):
                                    result += self.get_mapped(key,row[1][val])
                        objdict.setdefault(key, result)

            print (pagetitle, objdict)
            if updatepages:
                newpage = self.talker.create_page(self.match["parentpage"], pagetitle)
            resp = self.talker.get_response(self.talker.get_resturl()+self.match["parentpage"]+"/pages/"+pagetitle, 
                                           asjson = False)
            if resp.ok:
                newpage = self.talker.get_resturl()+self.match["parentpage"]+"/pages/"+pagetitle
            if newpage:
                self.talker.add_object(newpage, self.match["objectclass"], 
                                       attributes = objdict, update=singleobject)
