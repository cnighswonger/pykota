#! /usr/bin/env python

# PyKota - Print Quotas for CUPS
#
# (c) 2003 Jerome Alet <alet@librelogiciel.com>
# You're welcome to redistribute this software under the
# terms of the GNU General Public Licence version 2.0
# or, at your option, any higher version.
#
# You can read the complete GNU GPL in the file COPYING
# which should come along with this software, or visit
# the Free Software Foundation's WEB site http://www.fsf.org
#
# $Id$
#
# $Log$
# Revision 1.4  2003/02/09 13:05:43  jalet
# Internationalization continues...
#
# Revision 1.3  2003/02/07 13:12:41  jalet
# Bad old comment
#
# Revision 1.2  2003/02/05 23:00:12  jalet
# Forgotten import
# Bad datetime conversion
#
# Revision 1.1  2003/02/05 21:28:17  jalet
# Initial import into CVS
#
#
#

import os
from pykota.requester import PyKotaRequesterError

class Requester :
    """A class to send queries to printers via SNMP."""
    def __init__(self, config, printername) :
        """Sets instance vars depending on the current printer."""
        self.printername = printername
        self.community = config.config.get(printername, "snmpcmnty")
        self.oid = config.config.get(printername, "snmpoid")
        
    def getPrinterPageCounter(self, hostname) :
        """Returns the page counter from the hostname printer via SNMP.
        
           Currently uses the snmpget external command. TODO : do it internally 
        """
        if hostname is None :
            raise PyKotaRequesterError, _("Unknown printer address in SNMP(%s, %s) for printer %s") % (self.community, self.oid, self.printername)
        answer = os.popen("snmpget -c %s -Ov %s %s" % (self.community, hostname, self.oid))
        try :
            pagecounter = int(answer.readline().split()[-1].strip())
        except IndexError :    
            raise PyKotaRequesterError, _("Unable to query printer %s via SNMP(%s, %s)") % (hostname, self.community, self.oid) 
        answer.close()
        return pagecounter
    
