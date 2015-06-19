#!/usr/bin/python
""" Load the performance information already gathered into a database. """
""" We assume we care about the data directory underneath us. """

import csv, dbconn, sys, os, glob
from simpleclub import Club

def normalize(str):
    if str:
        return ' '.join(str.split())
    else:
        return ''

def different(new, old, headers):
    """ Returns a list of items which have changed, each of which is a tuple of (item, old, new)."""
    res = []
    for h in headers:
        if new.__dict__[h] != old.__dict__[h]:
            #print h ,'is different for club', new.clubnumber
            #print 'old = %s, new = %s' % (old.__dict__[h], new.__dict__[h])
            res.append((h, old.__dict__[h], new.__dict__[h]))
    return res
    
def cleandate(date):
    charterdate = date.split('/')  
    if len(charterdate[2]) == 2:
        charterdate[2] = "20" + charterdate[2]
    return '-'.join((charterdate[2],charterdate[0],charterdate[1]))
    
def cleanheaders(hline):
    headers = [p.lower().replace(' ','') for p in hline]
    headers = [p.replace('?','') for p in headers]
    headers = [p.replace('.','') for p in headers]
    headers = [p.replace('/','') for p in headers]
    return headers
    
def cleanitem(item):
    """ Return the item with leading zeros and spaces stripped if it's an integer; leave it alone otherwise. """
    try:
        item = '%d' % int(item)
    except ValueError:
        pass
    return item
        
def doHistoricalClubs(conn):
    clubfiles = glob.glob("clubs.*.csv")
    clubfiles.sort()
    curs = conn.cursor()
    firsttime = True

    for c in clubfiles:
        cdate = c.split('.')[1]
        curs.execute('SELECT COUNT(*) FROM loaded WHERE tablename="clubs" AND loadedfor=%s', (cdate,))
        if curs.fetchone()[0] > 0:
            continue
        infile = open(c, 'rU')
        doDailyClubs(infile, conn, cdate, firsttime)
        firsttime = False
        infile.close()
    
    # Commit all changes    
    conn.commit()


def doDailyClubs(infile, conn, cdate, firsttime=False):
    """ infile is a file-like object """
    from datetime import datetime, timedelta
    
    curs = conn.cursor()
    reader = csv.reader(infile)

    hline = reader.next()
    headers = cleanheaders(hline)

    try:
        clubcol = headers.index('clubnumber')    
    except ValueError:
        if not hline[0].startswith('{"Message"'):
            print "'clubnumber' not in '%s'" % hline
        return
    print "loading clubs for", cdate
    dbheaders = [p for p in headers]
    addrcol1 = dbheaders.index('address1')
    addrcol2 = dbheaders.index('address2')
    dbheaders[addrcol1] = 'address'
    del dbheaders[addrcol2]   # I know there's a more Pythonic way.
    dbheaders.append('firstdate')
    dbheaders.append('lastdate')     # For now...

    Club.setfields(dbheaders)

    
    # We need to get clubs for yesterday so we know whether to update an entry or
    #   start a new one.
    yesterday = datetime.strftime(datetime.strptime(cdate, '%Y-%m-%d') - timedelta(1),'%Y-%m-%d')
    clubhist = Club.getClubsOn(yesterday, curs)
   
    for row in reader:
        if len(row) < 20:
            break     # we're finished

        # Convert to unicode.  Toastmasters usually uses UTF-8 but occasionally uses Windows CP1252 on the wire.
        try:
            row = [unicode(t.strip(), "utf8") for t in row]
        except UnicodeDecodeError:
            row = [unicode(t.strip(), "CP1252") for t in row]
         
        if len(row) > 20:
            # Special case...Millbrae somehow snuck two club websites in!
            row[16] = row[16] + ',' + row[17]
            del row[17]
            
        #print row[addrcol1]
        #print row[addrcol2]
        # Now, clean up the address:
        address = ';'.join([x.strip() for x in row[addrcol1].split('  ') + row[addrcol2].split('  ')])
        address = ';'.join([x.strip() for x in address.split(',')])
        address = ', '.join(address.split(';'))
        row[addrcol1] = address
        del row[addrcol2]
        
            
        # Get the right number of items into the row by setting today as the 
        #   tentative first and last date
        row.append(cdate)
        row.append(cdate)
        
        # And create the object
        club = Club(row)

        
        # Now, clean up things coming from Toastmasters

        if club.clubstatus.startswith('Open') or club.clubstatus.startswith('None'):
            club.clubstatus = 'Open'
        else:
            club.clubstatus = 'Restricted'
        
        # Clean up the club and district numbers and the area
        club.clubnumber = cleanitem(club.clubnumber)
        club.district = cleanitem(club.district)
        club.area = cleanitem(club.area)

    
        # Clean up the charter date
        club.charterdate = cleandate(club.charterdate)

    
        # Clean up advanced status
        club.advanced = '1' if (club.advanced != '') else '0'
    
    
    
        # And put it into the database if need be
        if club.clubnumber in clubhist:
            changes = different(club, clubhist[club.clubnumber], dbheaders[:-2])
        else:
            changes = []
        
        if changes:
            if not firsttime:
                curs.execute('INSERT IGNORE INTO clubchanges (clubnumber, changedate, item, old, new) VALUES (%s, %s, "New Club", "", "")', (club.clubnumber, cdate))
        if club.clubnumber not in clubhist or changes:
            club.firstdate = club.lastdate
            values = [club.__dict__[x] for x in dbheaders]
        
            thestr = 'INSERT IGNORE INTO clubs (' + ','.join(dbheaders) + ') VALUES (' + ','.join(['%s' for each in values]) + ');'
            try:
                curs.execute(thestr, values)
            except Exception, e:
                print e
            # Capture changes
            for (item, old, new) in changes:
                try:
                    curs.execute('INSERT IGNORE INTO clubchanges (clubnumber, changedate, item, old, new) VALUES (%s, %s, %s, %s, %s)', (club.clubnumber, cdate, item, old, new))
                except Exception, e:
		            print e
            clubhist[club.clubnumber] = club
            if different(club, clubhist[club.clubnumber], dbheaders[:-2]):
                print 'it\'s different after being set.'
                sys.exit(3) 
        else:
            # update the lastdate
            curs.execute('UPDATE clubs SET lastdate = %s WHERE clubnumber = %s AND lastdate = %s;', (cdate, club.clubnumber, yesterday))
    
    # If all the files were processed, today's work is done.    
    curs.execute('INSERT IGNORE INTO loaded (tablename, loadedfor) VALUES ("clubs", %s)', (cdate,))
        

def doHistoricalDistrictPerformance(conn):
    perffiles = glob.glob("distperf.*.csv")
    perffiles.sort()
    curs = conn.cursor()

    for c in perffiles:
        cdate = c.split('.')[1]
        curs.execute('SELECT COUNT(*) FROM loaded WHERE tablename="distperf" AND loadedfor=%s', (cdate,))
        if curs.fetchone()[0] > 0:
            continue
        infile = open(c, 'rU')
        doDailyDistrictPerformance(infile, conn, cdate)
        infile.close()

    # Commit all changes    
    conn.commit()
    
def doDailyDistrictPerformance(infile, conn, cdate):
    curs = conn.cursor()
    reader = csv.reader(infile)
    hline = reader.next()
    headers = cleanheaders(hline)
    # Do some renaming
    renames = (('club', 'clubnumber'),
               ('new', 'newmembers'),('lateren', 'laterenewals'),('octren', 'octrenewals'),
               ('aprren', 'aprrenewals'),('totalren', 'totalrenewals'),('totalchart', 'totalcharter'),
               ('distinguishedstatus', 'dist'), ('charterdatesuspenddate', 'action'))
    for (old, new) in renames:
        try:
            index = headers.index(old)
            headers[index] = new
        except:
            pass
    try:
        clubcol = headers.index('clubnumber')    
    except ValueError:
        print "'clubnumber' not in '%s'" % hline
        return
    print "loading distperf for", cdate    
    areacol = headers.index('area')
    districtcol = headers.index('district')
    # We're going to use the last column for the effective date of the data
    headers.append('asof')
    valstr = ','.join(['%s' for each in headers])
    headstr = ','.join(headers)
    for row in reader:
        if row[0].startswith("Month"):
            break
        action = row[-1].split()  # For later...
        row.append(cdate)
        row[areacol] = cleanitem(row[areacol])
        row[clubcol] = cleanitem(row[clubcol])
        row[districtcol] = cleanitem(row[districtcol])
        curs.execute('INSERT IGNORE INTO distperf (' + headstr + ') VALUES (' + valstr + ')', row)
        
        
        # If this item represents a suspended club, and it's the first time we've seen this suspension,
        # add it to the clubchanges database
        if 'Susp' in action:
            clubnumber = row[clubcol]
            suspdate = cleandate(action[action.index('Susp') + 1])
            curs.execute('SELECT * FROM clubchanges WHERE clubnumber=%s and item="Suspended" and new=%s', (clubnumber, suspdate))
            if not curs.fetchone():
                # Add this suspension
                curs.execute('INSERT IGNORE INTO clubchanges (item, old, new, clubnumber, changedate) VALUES ("Suspended", "", %s, %s, %s)', (suspdate, clubnumber, cdate))
                
    conn.commit()
    # Now, insert the month into all of today's entries
    month = row[0].split()[-1]  # Month of Apr, for example
    curs.execute('UPDATE distperf SET month = %s WHERE asof = %s', (month, cdate))
    curs.execute('INSERT IGNORE INTO loaded (tablename, loadedfor) VALUES ("distperf", %s)', (cdate,))
    conn.commit() 

    
def doHistoricalClubPerformance(conn):
    perffiles = glob.glob("clubperf.*.csv")
    perffiles.sort()
    curs = conn.cursor()

    for c in perffiles:
        cdate = c.split('.')[1]
        curs.execute('SELECT COUNT(*) FROM loaded WHERE tablename="clubperf" AND loadedfor=%s', (cdate,))
        if curs.fetchone()[0] > 0:
            continue
        infile = open(c, 'rU')
        doDailyClubPerformance(infile, conn, cdate)
        infile.close()

    # Commit all changes    
    conn.commit()
    
def doDailyClubPerformance(infile, conn, cdate):
    curs = conn.cursor()
    reader = csv.reader(infile)
    hline = reader.next()
    headers = cleanheaders(hline)
    try:
        clubcol = headers.index('clubnumber')    
    except ValueError:
        print "'clubnumber' not in '%s'" % hline
        return
    print "loading clubperf for", cdate
    areacol = headers.index('area')
    districtcol = headers.index('district')
    memcol = headers.index('activemembers')
    otr1col = headers.index('offtrainedround1')
    otr2col = headers.index('offtrainedround2')
    octduescol = headers.index('memduesontimeoct')
    aprduescol = headers.index('memduesontimeapr')
    offlistcol = headers.index('offlistontime')
    # We're going to use the last column for the effective date of the data
    headers.append('asof')
    headers.append('color')
    headers.append('goal9')
    headers.append('goal10')
    valstr = ','.join(['%s' for each in headers])
    headstr = ','.join(headers)
    for row in reader:
        if row[0].startswith("Month"):
            break
            
        row.append(cdate)
        row[areacol] = cleanitem(row[areacol])
        row[clubcol] = cleanitem(row[clubcol])
        row[districtcol] = cleanitem(row[districtcol])
        clubnumber = row[clubcol]        
        # Compute Colorcode
        members = int(row[memcol])
        if members <= 12:
            row.append('Red')
        elif members < 20:
            row.append('Yellow')
        else:
            row.append('Green')
            
        # Compute Goal 9 (training):
        if int(row[otr1col]) >= 4 and int(row[otr2col] >= 4):
            row.append(1)
        else:
            row.append(0)
            
        # Compute Goal 10 (paperwork):
        if ((int(row[octduescol]) > 0) or (int(row[aprduescol]) > 0)) and int(row[offlistcol]) > 0:
            row.append(1)
        else:
            row.append(0)
        
        curs.execute('INSERT IGNORE INTO clubperf (' + headstr + ') VALUES (' + valstr + ')', row)
        
        # Let's see if the club status has changed; if so, indicate that in the clubchanges table.
        curs.execute('SELECT clubstatus, asof FROM clubperf WHERE clubnumber=%s ORDER BY ASOF DESC LIMIT 2 ', (clubnumber,) )
        ans = curs.fetchall()
        if len(ans) == 2:
            if ans[0][0] != ans[1][0]:
                curs2 = conn.cursor()
                curs2.execute('INSERT IGNORE INTO clubchanges (item, old, new, clubnumber, changedate) VALUES ("Status Change", %s, %s, %s, %s)', (ans[1][0], ans[0][0], clubnumber, cdate))
        
    conn.commit()
    # Now, insert the month into all of today's entries
    month = row[0].split()[-1]  # Month of Apr, for example
    curs.execute('UPDATE clubperf SET month = %s WHERE asof = %s', (month, cdate))
    curs.execute('INSERT IGNORE INTO loaded (tablename, loadedfor) VALUES ("clubperf", %s)', (cdate,))
    conn.commit()
    
def doHistoricalAreaPerformance(conn):
    perffiles = glob.glob("areaperf.*.csv")
    perffiles.sort()
    curs = conn.cursor()

    for c in perffiles:
        cdate = c.split('.')[1]
        curs.execute('SELECT COUNT(*) FROM loaded WHERE tablename="areaperf" AND loadedfor=%s', (cdate,))
        if curs.fetchone()[0] > 0:
            continue
        infile = open(c, 'rU')
        doDailyAreaPerformance(infile, conn, cdate)
        infile.close()

    # Commit all changes    
    conn.commit()
    
def doDailyAreaPerformance(infile, conn, cdate):
    curs = conn.cursor()
    reader = csv.reader(infile)
    hline = reader.next()
    headers = cleanheaders(hline)
    try:
        clubcol = headers.index('club')   
        headers[clubcol] = 'clubnumber' 
    except ValueError:
        print "'club' not in '%s'" % hline
        return
    print "loading areaperf for", cdate
    areacol = headers.index('area')
    districtcol = headers.index('district')

    # We're going to use the last column for the effective date of the data
    headers.append('asof')
    valstr = ','.join(['%s' for each in headers])
    headstr = ','.join(headers)
    for row in reader:
        if row[0].startswith("Month"):
            break
            
        row.append(cdate)
        row[areacol] = cleanitem(row[areacol])
        row[clubcol] = cleanitem(row[clubcol])
        row[districtcol] = cleanitem(row[districtcol])
        clubnumber = row[clubcol]        
       
        
        curs.execute('INSERT IGNORE INTO areaperf (' + headstr + ') VALUES (' + valstr + ')', row)
        
       
    conn.commit()
    # Now, insert the month into all of today's entries
    month = row[0].split()[-1]  # Month of Apr, for example
    curs.execute('UPDATE areaperf SET month = %s WHERE asof = %s', (month, cdate))
    curs.execute('INSERT IGNORE INTO loaded (tablename, loadedfor) VALUES ("areaperf", %s)', (cdate,))
    conn.commit()
 
if __name__ == "__main__":
 
    import tmparms
    # Make it easy to run under TextMate
    if 'TM_DIRECTORY' in os.environ:
        os.chdir(os.path.join(os.environ['TM_DIRECTORY'],'data'))
        
    reload(sys).setdefaultencoding('utf8')
    
    # Handle parameters
    parms = tmparms.tmparms()
    parms.parse()
    print 'Connecting to %s:%s as %s' % (parms.dbhost, parms.dbname, parms.dbuser)
    conn = dbconn.dbconn(parms.dbhost, parms.dbuser, parms.dbpass, parms.dbname)
        
    doHistoricalClubs(conn)
    doHistoricalDistrictPerformance(conn)
    doHistoricalClubPerformance(conn)
    doHistoricalAreaPerformance(conn)

    conn.close()
    