# PyKota
#
# PyKota : Print Quotas for CUPS and LPRng
#
# (c) 2003 Jerome Alet <alet@librelogiciel.com>
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
# $Log$
# Revision 1.24  2003/04/29 18:37:54  jalet
# Pluggable accounting methods (actually doesn't support external scripts)
#
# Revision 1.23  2003/04/24 11:53:48  jalet
# Default policy for unknown users/groups is to DENY printing instead
# of the previous default to ALLOW printing. This is to solve an accuracy
# problem. If you set the policy to ALLOW, jobs printed by in nexistant user
# (from PyKota's POV) will be charged to the next user who prints on the
# same printer.
#
# Revision 1.22  2003/04/23 22:13:57  jalet
# Preliminary support for LPRng added BUT STILL UNTESTED.
#
# Revision 1.21  2003/03/29 13:45:27  jalet
# GPL paragraphs were incorrectly (from memory) copied into the sources.
# Two README files were added.
# Upgrade script for PostgreSQL pre 1.01 schema was added.
#
# Revision 1.20  2003/03/29 13:08:28  jalet
# Configuration is now expected to be found in /etc/pykota.conf instead of
# in /etc/cups/pykota.conf
# Installation script can move old config files to the new location if needed.
# Better error handling if configuration file is absent.
#
# Revision 1.19  2003/03/16 09:56:52  jalet
# Mailto option now accepts some additional values which all mean that
# nobody will receive any email message.
# Mailto option now works. Version 1.01 is now officially out.
#
# Revision 1.18  2003/03/16 08:00:50  jalet
# Default hard coded options are now used if they are not set in the
# configuration file.
#
# Revision 1.17  2003/03/15 23:01:28  jalet
# New mailto option in configuration file added.
# No time to test this tonight (although it should work).
#
# Revision 1.16  2003/02/17 23:01:56  jalet
# Typos
#
# Revision 1.15  2003/02/17 22:55:01  jalet
# More options can now be set per printer or globally :
#
#       admin
#       adminmail
#       gracedelay
#       requester
#
# the printer option has priority when both are defined.
#
# Revision 1.14  2003/02/17 22:05:50  jalet
# Storage backend now supports admin and user passwords (untested)
#
# Revision 1.13  2003/02/10 11:47:39  jalet
# Moved some code down into the requesters
#
# Revision 1.12  2003/02/10 10:36:33  jalet
# Small problem wrt external requester
#
# Revision 1.11  2003/02/10 08:50:45  jalet
# External requester seems to be finally ok now
#
# Revision 1.10  2003/02/10 08:19:57  jalet
# tell ConfigParser to return raw data, this allows our own strings
# interpolations in the requester
#
# Revision 1.9  2003/02/10 00:44:38  jalet
# Typos
#
# Revision 1.8  2003/02/10 00:42:17  jalet
# External requester should be ok (untested)
# New syntax for configuration file wrt requesters
#
# Revision 1.7  2003/02/09 13:05:43  jalet
# Internationalization continues...
#
# Revision 1.6  2003/02/07 22:00:09  jalet
# Bad cut&paste
#
# Revision 1.5  2003/02/06 23:58:05  jalet
# repykota should be ok
#
# Revision 1.4  2003/02/06 09:19:02  jalet
# More robust behavior (hopefully) when the user or printer is not managed
# correctly by the Quota System : e.g. cupsFilter added in ppd file, but
# printer and/or user not 'yet?' in storage.
#
# Revision 1.3  2003/02/05 23:26:22  jalet
# Incorrect handling of grace delay
#
# Revision 1.2  2003/02/05 23:09:20  jalet
# Name conflict
#
# Revision 1.1  2003/02/05 21:28:17  jalet
# Initial import into CVS
#
#
#

import sys
import os
import ConfigParser

class PyKotaConfigError(Exception):
    """An exception for PyKota config related stuff."""
    def __init__(self, message = ""):
        self.message = message
        Exception.__init__(self, message)
    def __repr__(self):
        return self.message
    __str__ = __repr__
    
class PyKotaConfig :
    """A class to deal with PyKota's configuration."""
    def __init__(self, directory) :
        """Reads and checks the configuration file."""
        self.filename = os.path.join(directory, "pykota.conf")
        if not os.path.isfile(self.filename) :
            raise PyKotaConfigError, _("Configuration file %s not found.") % self.filename
        self.config = ConfigParser.ConfigParser()
        self.config.read([self.filename])
                        
    def getPrinterNames(self) :    
        """Returns the list of configured printers, i.e. all sections names minus 'global'."""
        return [pname for pname in self.config.sections() if pname != "global"]
        
    def getGlobalOption(self, option, ignore=0) :    
        """Returns an option from the global section, or raises a PyKotaConfigError if ignore is not set, else returns None."""
        try :
            return self.config.get("global", option, raw=1)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) :    
            if ignore :
                return
            else :
                raise PyKotaConfigError, _("Option %s not found in section global of %s") % (option, self.filename)
                
    def getPrinterOption(self, printer, option) :    
        """Returns an option from the printer section, or the global section, or raises a PyKotaConfigError."""
        globaloption = self.getGlobalOption(option, ignore=1)
        try :
            return self.config.get(printer, option, raw=1)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) :    
            if globaloption is not None :
                return globaloption
            else :
                raise PyKotaConfigError, _("Option %s not found in section %s of %s") % (option, printer, self.filename)
        
    def getStorageBackend(self) :    
        """Returns the storage backend information as a Python mapping."""        
        backendinfo = {}
        for option in [ "storagebackend", "storageserver", \
                        "storagename", "storageadmin", \
                        "storageuser", \
                      ] :
            backendinfo[option] = self.getGlobalOption(option)
        for option in [ "storageadminpw", "storageuserpw" ] :    
            backendinfo[option] = self.getGlobalOption(option, ignore=1)
        return backendinfo
        
    def getLoggingBackend(self) :    
        """Returns the logging backend information."""
        validloggers = [ "stderr", "system" ] 
        try :
            logger = self.getGlobalOption("logger").lower()
        except PyKotaConfigError :    
            logger = "system"
        if logger not in validloggers :             
            raise PyKotaConfigError, _("Option logger only supports values in %s") % str(validloggers)
        return logger    
        
    def getAccounterBackend(self, printer) :    
        """Returns the accounter backend to use for a given printer.
        
           if it is not set, it defaults to 'querying' which means ask printer
           for its internal lifetime page counter.
        """   
        validaccounters = [ "querying" ]     
        try :
            accounter = self.getPrinterOption(printer, "accounter").lower()
        except PyKotaConfigError :    
            accounter = "querying"
        if accounter not in validaccounters :
            raise PyKotaConfigError, _("Option accounter in section %s only supports values in %s") % (printer, str(validaccounters))
        return accounter
        
    def getRequesterBackend(self, printer) :    
        """Returns the requester backend to use for a given printer, with its arguments."""
        try :
            fullrequester = self.getPrinterOption(printer, "requester")
        except PyKotaConfigError :    
            # No requester defined, maybe it is not needed if accounting method
            # is not set to 'querying', but if we are called, then the accounting
            # method really IS 'querying', and so there's a big problem.
            raise PyKotaConfigError, _("Option requester for printer %s was not set") % printer
        else :    
            try :
                (requester, args) = [x.strip() for x in fullrequester.split('(', 1)]
            except ValueError :    
                raise PyKotaConfigError, _("Invalid requester %s for printer %s") % (fullrequester, printer)
            if args.endswith(')') :
                args = args[:-1]
            if not args :
                raise PyKotaConfigError, _("Invalid requester %s for printer %s") % (fullrequester, printer)
            validrequesters = [ "snmp", "external" ] # TODO : add more requesters
            if requester not in validrequesters :
                raise PyKotaConfigError, _("Option requester for printer %s only supports values in %s") % (printer, str(validrequesters))
            return (requester, args)
        
    def getPrinterPolicy(self, printer) :    
        """Returns the default policy for the current printer."""
        validpolicies = [ "ALLOW", "DENY" ]     
        try :
            policy = self.getPrinterOption(printer, "policy").upper()
        except PyKotaConfigError :    
            policy = "DENY"
        if policy not in validpolicies :
            raise PyKotaConfigError, _("Option policy in section %s only supports values in %s") % (printer, str(validpolicies))
        return policy
        
    def getSMTPServer(self) :    
        """Returns the SMTP server to use to send messages to users."""
        try :
            return self.getGlobalOption("smtpserver")
        except PyKotaConfigError :    
            return "localhost"
        
    def getAdminMail(self, printer) :    
        """Returns the Email address of the Print Quota Administrator."""
        try :
            return self.getPrinterOption(printer, "adminmail")
        except PyKotaConfigError :    
            return "root@localhost"
        
    def getAdmin(self, printer) :    
        """Returns the full name of the Print Quota Administrator."""
        try :
            return self.getPrinterOption(printer, "admin")
        except PyKotaConfigError :    
            return "root"
        
    def getMailTo(self, printer) :    
        """Returns the recipient of email messages."""
        validmailtos = [ "NOBODY", "NONE", "NOONE", "BITBUCKET", "DEVNULL", "BOTH", "USER", "ADMIN" ]
        try :
            mailto = self.getPrinterOption(printer, "mailto").upper()
        except PyKotaConfigError :    
            mailto = "BOTH"
        if mailto not in validmailtos :
            raise PyKotaConfigError, _("Option mailto in section %s only supports values in %s") % (printer, str(validmailtos))
        return mailto    
        
    def getGraceDelay(self, printer) :    
        """Returns the grace delay in days."""
        try :
            gd = self.getPrinterOption(printer, "gracedelay")
        except PyKotaConfigError :    
            gd = 7
        try :
            return int(gd)
        except ValueError :    
            raise PyKotaConfigError, _("Invalid grace delay %s") % gd
