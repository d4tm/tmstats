#!/usr/bin/env python
""" Print the latest date and the month that goes with it, based on
    the 'loaded' table.  

"""
import tmparms, dbconn, os, sys, tmutil, MySQLdb




def getlatest(table, conn):
    curs = conn.cursor()
    # The MySQLdb library doesn't allow interpolating the table name, so we do
    # it via normal Python.
    statement = 'select t.monthstart, l.latest FROM %s t INNER JOIN (select max(loadedfor) as latest FROM loaded WHERE tablename="%s") l ON t.asof = l.latest GROUP BY t.monthstart, l.latest' % (table, table)
    try:
        curs.execute(statement)
        ans = curs.fetchone()
        ans = [tmutil.stringify(x) for x in ans]
    except (MySQLdb.Error, TypeError), e:
        sys.stderr.write(repr(e))
        ans = ('', '')
    return ans

if __name__ == '__main__':
    if 'TM_DIRECTORY' in os.environ:
        os.chdir(os.path.join(os.environ['TM_DIRECTORY'],'data'))

    parms = tmparms.tmparms()
    # Allow specifying a table.
    parms.add_argument('--table', dest='table', default='clubperf')
    parms.parse()
    conn = dbconn.dbconn(parms.dbhost, parms.dbuser, parms.dbpass, parms.dbname)
    
    ans = getlatest(parms.table, conn)
    print ' '.join(ans)
