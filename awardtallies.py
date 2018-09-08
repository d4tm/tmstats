#!/usr/bin/env python

# Create the "awards by division" and "awards by type" CSVs

import dbconn, tmutil, sys, os, datetime,awardinfo
from awardinfo import Awardinfo

def inform(*args, **kwargs):
    """ Print information to 'file' unless suppressed by the -quiet option.
          suppress is the minimum number of 'quiet's that need be specified for
          this message NOT to be printed. """
    suppress = kwargs.get('suppress', 1)
    file = kwargs.get('file', sys.stderr)
    
    if parms.quiet < suppress:
        print >> file, ' '.join(args)

### Insert classes and functions here.  The main program begins in the "if" statement below.

if __name__ == "__main__":
 
    import tmparms, argparse
    # Make it easy to run under TextMate
    if 'TM_DIRECTORY' in os.environ:
        os.chdir(os.path.join(os.environ['TM_DIRECTORY'],'data'))
        
    reload(sys).setdefaultencoding('utf8')
    
    # Handle parameters
    parms = tmparms.tmparms()
    parms.add_argument('--quiet', '-q', action='count')
    parms.add_argument('--pathwaysfile', default='awardsbyPathwayslevels.csv', dest='pathwaysfile', type=argparse.FileType('w'), help="CSV file: awards by Pathways Levels")
    parms.add_argument('--divfile', default='awardsbydivision.csv', dest='divfile', type=argparse.FileType('w'), help="CSV file: awards by division")
    parms.add_argument('--typefile', default='awardsbytype.csv', dest='typefile', type=argparse.FileType('w'), help="CSV file: awards by type")
    parms.add_argument('--tmyear', default=None, dest='tmyear', type=int, help='TM Year (current if omitted)')
    # Add other parameters here
    parms.parse() 
   
    # Connect to the database        
    conn = dbconn.dbconn(parms.dbhost, parms.dbuser, parms.dbpass, parms.dbname)
    curs = conn.cursor()
    
    # Main program begins here.
    if parms.tmyear:
        tmyear = parms.tmyear
    else:
        today = datetime.datetime.today()
        if today.month <= 6:
            tmyear = today.year - 1
        else:
            tmyear = today.year


    # First, deal with awards by Division. Note the creation of the interim awardnoDups, which is a way to eliminate duplicates. Some members show up multiple times for same award, either due to bugs in data import or due to the fact that Tmi changed the award codes for pathways and just appended people with new codes which created dups. either way, this filters them. 

    parms.divfile.write('Division,Awards\n')
    curs.execute("SELECT division, count(*) FROM (SELECT * FROM awards WHERE tmyear = %s AND award != 'LDREXC' GROUP BY membername,awarddate) as awardnoDups GROUP BY division ORDER BY division", (tmyear,))
    for l in curs.fetchall():
        parms.divfile.write('Division %s,%d\n' % (l[0].replace(',',';'), l[1]))
    parms.divfile.close()
     
    # And then awards by type
    parms.typefile.write('Award,Achieved\n')
    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = %s AND award = 'CC'", (tmyear,))
    parms.typefile.write('Competent Communicator,%d\n'% curs.fetchone()[0])
    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = %s AND award LIKE 'AC%%'", (tmyear,))
    parms.typefile.write('Advanced Communicator,%d\n'% curs.fetchone()[0])
    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = %s AND award = 'CL'", (tmyear,))
    parms.typefile.write('Competent Leader,%d\n'% curs.fetchone()[0])
    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = %s AND award LIKE 'AL%%'", (tmyear,))
    parms.typefile.write('Advanced Leader,%d\n'% curs.fetchone()[0])
    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = %s AND award = 'DTM'", (tmyear,))
    parms.typefile.write('Distinguished Toastmaster,%d\n'% curs.fetchone()[0])
    parms.typefile.close()    
    
    #Now do pathways levels:
    level1WhereQuery=''
    level2WhereQuery=''
    level3WhereQuery=''
    level4WhereQuery=''
    level5WhereQuery=''
    for p in Awardinfo.paths:
	if p[2]=='1':
		level1WhereQuery+="'"+p+"',"
	elif p[2]=='2':
		level2WhereQuery+="'"+p+"',"
	elif p[2]=='3':
		level3WhereQuery+="'"+p+"',"
	elif p[2]=='4':
		level4WhereQuery+="'"+p+"',"
	elif p[2]=='5':
		level5WhereQuery+="'"+p+"',"

    level1WhereQuery=level1WhereQuery.rstrip(',')
    level2WhereQuery=level2WhereQuery.rstrip(',')
    level3WhereQuery=level3WhereQuery.rstrip(',')
    level4WhereQuery=level4WhereQuery.rstrip(',')
    level5WhereQuery=level5WhereQuery.rstrip(',')

    parms.pathwaysfile.write("Pathways Level,Achieved\n")
    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = {0} AND award in ({1})".format(tmyear,level1WhereQuery)) 
    parms.pathwaysfile.write('Pathways Level 1,%d\n'% curs.fetchone()[0])

    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = {0} AND award in ({1})".format(tmyear,level2WhereQuery)) 
    parms.pathwaysfile.write('Pathways Level 2,%d\n'% curs.fetchone()[0])

    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = {0} AND award in ({1})".format(tmyear,level3WhereQuery)) 
    parms.pathwaysfile.write('Pathways Level 3,%d\n'% curs.fetchone()[0])

    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = {0} AND award in ({1})".format(tmyear,level4WhereQuery)) 
    parms.pathwaysfile.write('Pathways Level 4,%d\n'% curs.fetchone()[0])

    curs.execute("SELECT COUNT(*) FROM awards WHERE tmyear = {0} AND award in ({1})".format(tmyear,level5WhereQuery)) 
    parms.pathwaysfile.write('Pathways Level 5,%d\n'% curs.fetchone()[0])
