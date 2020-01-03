#!/usr/bin/env python
import dbconn, tmparms, os, sys
from datetime import date, datetime
import argparse
from tmutil import showclubswithoutvalues

class myclub:
    """ Just enough club info to sort the list nicely """
    def __init__(self, clubnumber, clubname, asof, division, area):
        self.area = '%s%s' % (division, area)
        self.clubnumber = clubnumber
        self.clubname = clubname
        self.asof = asof

    def tablepart(self):
        return ('    <td>%s</td><td>%s</td>' % (self.area, self.clubname))

    def key(self):
        return (self.area, self.clubnumber)

# Make it easy to run under TextMate
if 'TM_DIRECTORY' in os.environ:
    os.chdir(os.path.join(os.environ['TM_DIRECTORY'],'data'))

reload(sys).setdefaultencoding('utf8')

# Handle parameters
parms = tmparms.tmparms()
parms.parser.add_argument("--fromend", dest='fromend', type=int, default=7)
parms.parser.add_argument("--toend", dest='toend', type=int, default=9)
parms.parser.add_argument("--outfile1", dest='outfile1', type=argparse.FileType('w'), default='lucky7round1.html')
parms.parser.add_argument("--outfile2", dest='outfile2', type=argparse.FileType('w'), default='lucky7round2.html')

parms.parse()

conn = dbconn.dbconn(parms.dbhost, parms.dbuser, parms.dbpass, parms.dbname)
curs = conn.cursor()

today = datetime.now()
# If we're in the next year, make "today" last year.
if today.month < parms.fromend:
    try:
        today = today.replace(year=today.year-1)
    except ValueError:  # Today must be Leap Day!
        today = today.replace(year=today.year-1, day=28)
startmonth = '%d-%0.2d-01' % (today.year, parms.fromend)
endmonth = '%d-%0.2d-01' % (today.year, parms.toend)

outfile1 = parms.outfile1
outfile2 = parms.outfile2

#get all clubs that had all 7 officers trained in round 1
curs.execute("SELECT c.clubnumber, c.clubname, c.asof, c.division, c.area from clubperf c inner join (select max(asof) as maxasof,clubnumber FROM clubperf where monthstart>%s and offtrainedround1=7 group by clubnumber) d on c.clubnumber = d.clubnumber and c.asof=d.maxasof ORDER by clubname",(startmonth,))


clubs = []
for c in curs.fetchall():
    clubs.append(myclub(*c))

title = '<h4>Lucky 7 - Round 1 (June-August %s)</h4>\n' % today.year
outfile1.write(title)
showclubswithoutvalues(clubs, outfile1)

#get all clubs that had all 7 officers trained in round 2
curs.execute("SELECT c.clubnumber, c.clubname, c.asof, c.division, c.area from clubperf c inner join (select max(asof) as maxasof,clubnumber FROM clubperf where monthstart>%s and offtrainedround2=7 group by clubnumber) d on c.clubnumber = d.clubnumber and c.asof=d.maxasof ORDER by clubname",(startmonth,))


clubs = []
for c in curs.fetchall():
    clubs.append(myclub(*c))

thisYear='%s' % str(today.year+1)
title = '<h4>Lucky 7 - Round 2 (November-February %s)</h4>\n' % thisYear.rstrip()
outfile2.write(title)
showclubswithoutvalues(clubs, outfile2)
