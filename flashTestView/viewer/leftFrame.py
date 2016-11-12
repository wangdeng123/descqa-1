#!/usr/bin/env python
import sys
import os
import re
import cgi, cgitb
cgitb.enable()
print "Content-type: text/html\n"

sys.path.insert(0, "../lib")
import littleParser, ezt

class FlashRun:
    """
    encapsulates one run of the Flash code against
    a single parfile. A list of FlashRun objects
    will form part of the data dictionary passed to
    the ezt template
    """
    def __init__(self, name):
        self.name = name

class File:
    """
    encapsulates the data needed to locate any files
    """
    def __init__(self, path_or_dir, basename=None):
        if basename is None:
            self.path = path_or_dir
            self.filename = os.path.basename(path_or_dir)
        else:
            self.path = os.path.join(path_or_dir, basename)
            self.filename = basename
        if self.filename.endswith('.png'):
            self.data = open(self.path, 'rb').read().encode("base64").replace("\n", "")


# -------------- web page starts ---------------- #
form = cgi.FieldStorage()
targetDir = form.getvalue("target_dir")

try:
    configDict = littleParser.parseFile("../config")
    siteTitle = configDict.get("siteTitle", '')
except:
    siteTitle = ''

print "<html>"
print "<head>"
print "<title>%s</title>" % siteTitle
print open("viewBuildStyle.css","r").read()
print "</head>"

# the data dictionary we will pass to the ezt template
templateData = {}

# fill in data that has to do with this build
# (i.e. setup and compilation data)
templateData["fullBuildPath"]       = targetDir
templateData["pathToInvocationDir"] = os.path.dirname(targetDir)
templateData["buildDir"]            = os.path.basename(targetDir)
templateData["invocationDir"]       = os.path.basename(os.path.dirname(targetDir))

# YYM: hack to get _group_by_catalog work 
templateData["isGroupByCatalog"] = None
GROUP_BY_CATALOG_DIRNAME = '_group_by_catalog'
if templateData["invocationDir"] == GROUP_BY_CATALOG_DIRNAME:
    templateData["isGroupByCatalog"] = True
    templateData["invocationDir"] = os.path.basename(os.path.dirname(templateData["pathToInvocationDir"]))
    templateData["pathToInvocationDir"] = os.path.dirname(templateData["pathToInvocationDir"])


# search for summary plot:
filepath = os.path.join(targetDir, "summary_plot.png")
templateData["summaryPlot"] = File(filepath) if os.path.isfile(filepath) else None
filepath = os.path.join(targetDir, "summary_plot.log")
templateData["summaryPlotLog"] = File(filepath) if os.path.isfile(filepath) else None


# we assume any directories in 'targetDir' to be the output
# of a single *run* of Flash (i.e., the output resulting from
# the Flash executable's being run against a single parfile)
# Information in this directory will be stored in a FlashRun
# object (see class definition at top of file)
runs = [FlashRun(item) for item in sorted(os.listdir(targetDir)) \
        if os.path.isdir(os.path.join(targetDir, item))]

for run in runs:
    run.fullPath = os.path.join(targetDir, run.name)
    run.datfiles = []            
    run.logfiles = []             
    run.imgfiles = []
    items = sorted(os.listdir(run.fullPath))
    for item in items:
        if item.endswith(".log"):
            run.logfiles.append(File(run.fullPath, item))
        elif any(item.endswith(ext) for ext in (".txt", ".dat", ".csv")):
            run.datfiles.append(File(run.fullPath, item))
        elif item.endswith(".png"):
            run.imgfiles.append(File(run.fullPath, item))

    try:
        with open(os.path.join(run.fullPath, "STATUS")) as f:
            run.status = f.readline().strip()
            run.summary = f.read().strip()
    except (OSError, IOError):
        run.status = 'NO_STATUS_FILE_ERROR'
        run.summary = ''

    for status, color in (('PASSED', 'green'), ('SKIPPED', 'gold'), ('FAILED', 'orangered'), ('ERROR', 'darkred')):
        if run.status.endswith(status):
            run.statusColor = color
            break

templateData["runs"] = runs or None

# print the html generated by ezt templates
ezt.Template("viewBuildTemplate.ezt").generate(sys.stdout, templateData)
print "</html>"

