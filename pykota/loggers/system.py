# PyKota
# -*- coding: ISO-8859-15 -*-
#
# PyKota : Print Quotas for CUPS and LPRng
#
# (c) 2003-2004 Jerome Alet <alet@librelogiciel.com>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# $Id$
#
#

import os
import syslog

class Logger :
    """A logger class which logs to syslog."""
    levels = { "error" : "ERR", "warn": "WARNING", "info": "INFO", "debug": "DEBUG" }
    def __init__(self) :
        """Opens the logging subsystem."""
        syslog.openlog("PyKota", 0, syslog.LOG_LPR)
        
    def __del__(self) :    
        """Ensures the logging subsystem is closed."""
        syslog.closelog()
        
    def log_message(self, message, level="info") :
        """Sends the message to syslog."""
        priority = getattr(syslog, "LOG_%s" % self.levels.get(level.lower(), "DEBUG").upper(), syslog.LOG_DEBUG)
        try :
            syslog.syslog(priority, "(PID %s) : %s" % (os.getpid(), message.strip()))
        except :    
            pass # What else could we do ?
