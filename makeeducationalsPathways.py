#!/usr/bin/env python
""" Make the 'Congratulations!' slide and the list of award-winners."""

# This is a standard skeleton to use in creating a new program in the TMSTATS suite.

import tmutil, sys, os, datetime, subprocess, codecs
import tmglobals, tmparms
from awardinfo import Awardinfo 
globals = tmglobals.tmglobals()


### Insert classes and functions here.  The main program begins in the "if" statement below.

awards = {}
knownawards = Awardinfo.lookup
awardorder = ['DTM', 1, 'CL', 'CC', 2, 'ALB', 'ACB', 3, 'ALS', 'ACS', 4, 'ACG', 5]


class Award:
    def __init__(self, membername, award, clubname, awarddate):
	self.membername = membername
        self.award = award
        self.level = Awardinfo.levels[award]
        self.clubname = clubname
        self.awarddate = awarddate
        self.key = self.membername + ';' + self.clubname + ';' + repr(self.awarddate)
        if self.level == 0:
            # Old award
            if award not in awards:
                awards[award] = []
            awards[award].append(self)
        else:
            if self.level not in awards:
                awards[self.level] = []
            awards[self.level].append(self)
 

    def show(self):
        return u'<tr><td>'+ unicode(self.membername) +u'</td><td>' + unicode(self.clubname) + u'</td><td>'+ unicode(Awardinfo.paths[self.award])+'</td></tr>' 

def printawards(awards, knownawards, k):
    if k in awards:
        print '<tr><td class="pathawardname" colspan="3">Level %d Awards</td></tr>' % k    
        for each in sorted(awards[k], key=lambda x:x.key):
            print each.show()

def makeCongratulations(count, district, timing, parms):
    # Now, create the "Congratulations" slide

    cmd = ['convert']
    cmd.append(parms.baseslide)
    cmd.append('-quality')
    cmd.append('50')
    cmd.append('-font')
    cmd.append('Helvetica-Bold')
    cmd.append('-pointsize')
    cmd.append('26')
    cmd.append('-fill')
    cmd.append('black')
    line1 = 100
    left = 380
    shadow = 2
    spacing = 32
    line = line1
    texts = ["Congratulations to the %d District %s" % (count, district),
             "members who achieved one or more of their",
             "educational goals %s." % (timing,),
             "",
             "Will you be recognized next?"]
    for t in texts:
        cmd.append('-draw')
        cmd.append('"text %d,%d \'%s\'"' % (left+shadow, line+shadow, t))
        line += spacing
    line = line1 + shadow
    cmd.append('-fill')
    cmd.append('white')
    for t in texts:
        cmd.append('-draw')
        cmd.append('"text %d,%d \'%s\'"' % (left, line, t))
        line += spacing
    cmd.append(parms.prefix + '.jpg')

    return cmd

if __name__ == "__main__":



    # Handle parameters
    parms = tmparms.tmparms()
    parms.add_argument('--quiet', '-q', action='count')
    group = parms.parser.add_mutually_exclusive_group()
    group.add_argument('--since', type=str, default='30',
            help='How long ago or first date to look for awards.')
    group.add_argument('--lastmonth', action='store_true',
            help='If specified, looks at the previous month')
    parms.add_argument('--include-hpl', action='store_true',
            help='If specified, include HPL awards.  Normally, they are excluded.')
    parms.add_argument('--prefix', type=str, default='recentawardsPathways',
            help='Filename prefix for the .jpg and .html files created by this program (default: %(default)s)')
    parms.add_argument('--baseslide', type=str, default='ed-achieve-base.png',
            help='Slide to use as the base for the "Congratulations" slide')

    # Do global setup
    globals.setup(parms)
    conn = globals.conn
    curs = globals.curs

    

    # Your main program begins here.
    # Close stdout and reassign it to the output file
    sys.stdout.close()
    sys.stdout = codecs.open(parms.prefix + '.shtml', 'w', 'utf-8')

    clauses = []
    # Figure out the timeframe for the queries.
    today = datetime.datetime.today()

    if parms.lastmonth:
        month = today.month - 1
        year = today.year
        if month <= 0:
            month = 12
            year = year - 1
        clauses.append('MONTH(awarddate) = %d' % month)
        timestamp = 'during ' + datetime.date(year, month, 1).strftime('%B, %Y')

    else:
        firstdate = datetime.datetime.strptime(tmutil.cleandate(parms.since), '%Y-%m-%d')
        clauses.append("awarddate >= '%s'" % firstdate.strftime('%Y-%m-%d'))
        timestamp = 'since {d:%B} {d.day}, {d.year}'.format(d=firstdate)


    if not parms.include_hpl:
        clauses.append('award != "LDREXC"')

#    if parms.district:
#        clauses.append('district = %s' % parms.district)

    #remove non pathways:
    clauses.append('award!="CL"')
    clauses.append('award!="CC"')
    clauses.append('award!="ALB"')
    clauses.append('award!="ACB"')
    clauses.append('award!="ALS"')
    clauses.append('award!="ACS"')
    clauses.append('award!="ACG"')
    
    #remove new pathway award designation (not sure this will work long term)
    clauses.append('award!="EC1"')
    clauses.append('award!="EC2"')
    clauses.append('award!="EC3"')
    clauses.append('award!="EC4"')
    clauses.append('award!="EC5"')
    
    clauses.append('award!="LD1"')
    clauses.append('award!="LD2"')
    clauses.append('award!="LD3"')
    clauses.append('award!="LD4"')
    clauses.append('award!="LD5"')
    
    clauses.append('award!="PI1"')
    clauses.append('award!="PI2"')
    clauses.append('award!="PI3"')
    clauses.append('award!="PI4"')
    clauses.append('award!="PI5"')
   
    clauses.append('award!="PM1"')
    clauses.append('award!="PM2"')
    clauses.append('award!="PM3"')
    clauses.append('award!="PM4"')
    clauses.append('award!="PM5"')
    
    clauses.append('award!="SR1"')
    clauses.append('award!="SR2"')
    clauses.append('award!="SR3"')
    clauses.append('award!="SR4"')
    clauses.append('award!="SR5"')


    clauses.append('award!="TC1"')
    clauses.append('award!="TC2"')
    clauses.append('award!="TC3"')
    clauses.append('award!="TC4"')
    clauses.append('award!="TC5"')

    clauses.append('award!="DL1"')
    clauses.append('award!="DL2"')
    clauses.append('award!="DL3"')
    clauses.append('award!="DL4"')
    clauses.append('award!="DL5"')

    clauses.append('award!="MS1"')
    clauses.append('award!="MS2"')
    clauses.append('award!="MS3"')
    clauses.append('award!="MS4"')
    clauses.append('award!="MS5"')

    clauses.append('award!="IP1"')
    clauses.append('award!="IP2"')
    clauses.append('award!="IP3"')
    clauses.append('award!="IP4"')
    clauses.append('award!="IP5"')

    clauses.append('award!="VC1"')
    clauses.append('award!="VC2"')
    clauses.append('award!="VC3"')
    clauses.append('award!="VC4"')
    clauses.append('award!="VC5"')

    clauses.append('award!="DTM"')

    curs.execute("SELECT COUNT(DISTINCT membername) FROM awards WHERE " + ' AND '.join(clauses))
    count = curs.fetchone()[0]

#I added this group by here, because there is a wierd bug in the update from tm that causes certain awards to be duplicated. This group by removes the duplicate. The duplication is such that a record with same membername,award,clubname,and awarddate appears more than once and that screws up the printout. So this group BY below i added resolves it. its a bandaid but its one that can work well. Actual fix is to see in the code that updates the awards table, why this duplication is inserted

    curs.execute("SELECT membername, award, clubname, awarddate FROM awards WHERE " + ' AND '.join(clauses) + "group BY membername,award,clubname,awarddate")
    for (membername, award, clubname, awarddate) in curs.fetchall():
        Award(membername, award, clubname, awarddate)



    print '<p style="color: #772432; font-size: 18pt;"><strong>Pathways Awards %s</strong></p>' % timestamp

    # And now print the awards themselves.

    print '<table style="width: 100%;">\n<tbody>\n'
    for k in awardorder:
        printawards(awards, knownawards, k)
    print '</tbody>\n</table>\n'


    cmd = makeCongratulations(count, parms.district, timestamp, parms)
    subprocess.call(' '.join(cmd),shell=True)
