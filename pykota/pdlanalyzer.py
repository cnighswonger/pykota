# PyKota
# -*- coding: ISO-8859-15 -*-
#
# PyKota - Print Quotas for CUPS and LPRng
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
# $Log$
# Revision 1.1  2004/05/18 09:59:54  jalet
# pkpgcounter is now just a wrapper around the PDLAnalyzer class
#
#
#

import sys
import os
import struct
import tempfile
    
class PostScriptAnalyzer :
    def __init__(self, infile) :
        """Initialize PostScript Analyzer."""
        self.infile = infile
        
    def getJobSize(self) :    
        """Count pages in a DSC compliant PostScript document."""
        pagecount = 0
        pagenum = None
        while 1 :
            line = self.infile.readline()
            if not line :
                break
            if line.startswith("%%Page: ") :
                pagecount += 1
        return pagecount
        
class PCLAnalyzer :
    def __init__(self, infile) :
        """Initialize PCL Analyzer."""
        self.infile = infile
        
    def getJobSize(self) :     
        """Count pages in a PCL5 document."""
        #
        # Algorithm from pclcount
        # (c) 2003, by Eduardo Gielamo Oliveira & Rodolfo Broco Manin 
        # published under the terms of the GNU General Public Licence v2.
        # 
        # Backported from C to Python by Jerome Alet, then enhanced
        # with more PCL tags detected. I think all the necessary PCL tags
        # are recognized to correctly handle PCL5 files wrt their number
        # of pages. The documentation used for this was :
        #
        # HP PCL/PJL Reference Set
        # PCL5 Printer Language Technical Quick Reference Guide
        # http://h20000.www2.hp.com/bc/docs/support/SupportManual/bpl13205/bpl13205.pdf 
        #
        tagsends = { "&n" : "W", 
                     "&b" : "W", 
                     "*i" : "W", 
                     "*l" : "W", 
                     "*m" : "W", 
                     "*v" : "W", 
                     "*c" : "W", 
                     "(f" : "W", 
                     "*b" : "VW",
                     "(s" : "W", 
                     ")s" : "W", 
                     "&p" : "X", 
                     "&l" : "X" } 
        copies = 1
        pagecount = resets = 0
        tag = None
        while 1 :
            char = self.infile.read(1)
            if not char :       # EOF ?
                break   
            if char == "\014" :    
                pagecount += 1
            elif char == "\033" :    
                #
                #     <ESC>*b###W -> Start of a raster data row/block
                #     <ESC>*b###V -> Start of a raster data plane
                #     <ESC>*c###W -> Start of a user defined pattern
                #     <ESC>*i###W -> Start of a viewing illuminant block
                #     <ESC>*l###W -> Start of a color lookup table
                #     <ESC>*m###W -> Start of a download dither matrix block
                #     <ESC>*v###W -> Start of a configure image data block
                #     <ESC>(s###W -> Start of a characters description block
                #     <ESC>)s###W -> Start of a fonts description block
                #     <ESC>(f###W -> Start of a symbol set block
                #     <ESC>&b###W -> Start of configuration data block
                #     <ESC>&l###X -> Number of copies
                #     <ESC>&n###W -> Starts an alphanumeric string ID block
                #     <ESC>&p###X -> Start of a non printable characters block
                #
                tagstart = self.infile.read(1)
                if tagstart in "E9=YZ" : # one byte PCL tag
                    if tagstart == "E" :
                        resets += 1
                    continue             # skip to next tag
                tag = tagstart + self.infile.read(1)
                try :
                    tagend = tagsends[tag]
                except KeyError :    
                    pass    # Unsupported PCL tag
                else :    
                    # Now read the numeric argument
                    size = 0
                    while 1 :
                        char = self.infile.read(1)
                        if not char.isdigit() :
                            break
                        size = (size * 10) + int(char)    
                    if char in tagend :    
                        if tag == "&l" :
                            copies = size
                        else :    
                            # doing a read will prevent the seek 
                            # for unseekable streams. 
                            # we just ignore the block anyway.
                            if tag == "&n" : 
                                # we have to take care of the operation id byte
                                # which is before the string itself
                                size += 1
                            self.infile.read(size) # skips block, while avoiding seek()
                            
        # if pagecount is still 0, we will return the number
        # of resets instead of the number of form feed characters.
        # but the number of resets is always at least 2 with a valid
        # pcl file : one at the very start and one at the very end
        # of the job's data. So we substract 2 from the number of
        # resets. And since on our test data we needed to substract
        # 1 more, we finally substract 3, and will test several
        # PCL files with this. If resets < 2, then the file is
        # probably not a valid PCL file, so we return 0
        if not pagecount :
            return copies * (resets - 3) * (resets > 2)
        else :
            return copies * pagecount
        
class PCLXLAnalyzer :
    def __init__(self, infile) :
        """Initialize PCLXL Analyzer."""
        raise TypeError, "PCLXL (aka PCL6) is not supported yet."
        self.infile = infile
        self.islittleendian = None
        found = 0
        while not found :
            line = self.infile.readline()
            if not line :
                break
            if line[1:12] == " HP-PCL XL;" :
                found = 1
                if line[0] == ")" :
                    self.littleendian()
                elif line[0] == "(" :    
                    self.bigendian()
        if not found :
            raise TypeError, "This file doesn't seem to be PCLXL (aka PCL6)"
        else :    
            self.tags = [None] * 256    
            self.tags[0x28] = self.bigendian    # big endian
            self.tags[0x29] = self.littleendian # big endian
            self.tags[0x43] = self.beginPage    # BeginPage
            self.tags[0x44] = self.endPage      # EndPage
            
            self.tags[0xc0] = 1 # ubyte
            self.tags[0xc1] = 2 # uint16
            self.tags[0xc2] = 4 # uint32
            self.tags[0xc3] = 2 # sint16
            self.tags[0xc4] = 4 # sint32
            self.tags[0xc5] = 4 # real32
            
            self.tags[0xc8] = self.array_8  # ubyte_array
            self.tags[0xc9] = self.array_16 # uint16_array
            self.tags[0xca] = self.array_32 # uint32_array
            self.tags[0xcb] = self.array_16 # sint16_array
            self.tags[0xcc] = self.array_32 # sint32_array
            self.tags[0xcd] = self.array_32 # real32_array
            
            self.tags[0xd0] = 2 # ubyte_xy
            self.tags[0xd1] = 4 # uint16_xy
            self.tags[0xd2] = 8 # uint32_xy
            self.tags[0xd3] = 4 # sint16_xy
            self.tags[0xd4] = 8 # sint32_xy
            self.tags[0xd5] = 8 # real32_xy
            
            self.tags[0xd0] = 4  # ubyte_box
            self.tags[0xd1] = 8  # uint16_box
            self.tags[0xd2] = 16 # uint32_box
            self.tags[0xd3] = 8  # sint16_box
            self.tags[0xd4] = 16 # sint32_box
            self.tags[0xd5] = 16 # real32_box
            
            self.tags[0xf8] = 1 # attr_ubyte
            self.tags[0xf9] = 2 # attr_uint16
            
            self.tags[0xfa] = self.embeddedData      # dataLength
            self.tags[0xfb] = self.embeddedDataSmall # dataLengthByte
            
    def debug(self, msg) :
        """Outputs a debug message on stderr."""
        sys.stderr.write("%s\n" % msg)
        sys.stderr.flush()
        
    def beginPage(self) :
        """Indicates the beginning of a new page."""
        self.pagecount += 1
        self.debug("Begin page %i at %s" % (self.pagecount, self.infile.tell()))
        
    def endPage(self) :
        """Indicates the end of a page."""
        self.debug("End page %i at %s" % (self.pagecount, self.infile.tell()))
        
    def handleArray(self, itemsize) :        
        """Handles arrays."""
        datatype = self.infile.read(1)
        length = self.tags[ord(datatype)]
        sarraysize = self.infile.read(length)
        if self.islittleendian :
            fmt = "<"
        else :    
            fmt = ">"
        if length == 1 :    
            fmt += "B"
        elif length == 2 :    
            fmt += "H"
        elif length == 4 :    
            fmt += "I"
        else :    
            raise TypeError, "Error on array size at %s" % self.infile.tell()
        arraysize = struct.unpack(fmt, sarraysize)[0]
        return arraysize * itemsize
        
    def array_8(self) :    
        """Handles byte arrays."""
        return self.handleArray(1)
        
    def array_16(self) :    
        """Handles byte arrays."""
        return self.handleArray(2)
        
    def array_32(self) :    
        """Handles byte arrays."""
        return self.handleArray(4)
        
    def embeddedDataSmall(self) :
        """Handle small amounts of data."""
        return ord(self.infile.read(1))
        
    def embeddedData(self) :
        """Handle normal amounts of data."""
        if self.islittleendian :
            fmt = "<I"
        else :    
            fmt = ">I"
        return struct.unpack(fmt, self.infile.read(4))[0]
        
    def littleendian(self) :        
        """Toggles to little endianness."""
        self.islittleendian = 1 # little endian
        
    def bigendian(self) :    
        """Toggles to big endianness."""
        self.islittleendian = 0 # big endian
    
    def getJobSize(self) :
        """Counts pages in a PCLXL (PCL6) document."""
        self.pagecount = 0
        while 1 :
            pos = self.infile.tell()
            char = self.infile.read(1)
            if not char :
                break
            index = ord(char)    
            length = self.tags[index]
            if length is not None :
                if not length :
                    self.debug("Unrecognized tag 0x%02x at %s\n" % (index, self.infile.tell()))
                elif callable(length) :    
                    length = length()
                if length :    
                    self.infile.read(length)    
        return self.pagecount
    
class PDLAnalyzer :    
    """Generic PDL Analyzer class."""
    def __init__(self, filename) :
        """Initializes the PDL analyzer."""
        self.filename = filename
        
    def getJobSize(self) :    
        """Returns the job's size."""
        self.openFile()
        pdlhandler = self.detectPDLHandler()
        if pdlhandler is not None :
            try :
                size = pdlhandler(self.infile).getJobSize()
            finally :    
                self.closeFile()
            return size
        else :        
            self.closeFile()
            raise TypeError, "ERROR : Unknown file format for %s" % self.filename
        
    def openFile(self) :    
        """Opens the job's data stream for reading."""
        if self.filename == "-" :
            # we must read from stdin
            # but since stdin is not seekable, we have to use a temporary
            # file instead.
            self.infile = tempfile.TemporaryFile()
            while 1 :
                data = sys.stdin.read(256 * 1024) 
                if not data :
                    break
                self.infile.write(data)
            self.infile.flush()    
            self.infile.seek(0)
        else :    
            # normal file
            self.infile = open(self.filename, "rb")
            
    def closeFile(self) :        
        """Closes the job's data stream."""
        self.infile.close()    
        
    def isPostScript(self, data) :    
        """Returns 1 if data is PostScript, else 0."""
        if data.startswith("%!") or \
           data.startswith("\004%!") or \
           data.startswith("\033%-12345X%!PS") or \
           ((data[:128].find("\033%-12345X") != -1) and \
             ((data.find("LANGUAGE=POSTSCRIPT") != -1) or \
              (data.find("LANGUAGE = POSTSCRIPT") != -1) or \
              (data.find("LANGUAGE = Postscript") != -1))) :
            return 1
        else :    
            return 0
        
    def isPCL(self, data) :    
        """Returns 1 if data is PCL, else 0."""
        if data.startswith("\033E\033") or \
           ((data[:128].find("\033%-12345X") != -1) and \
             ((data.find("LANGUAGE=PCL") != -1) or \
              (data.find("LANGUAGE = PCL") != -1) or \
              (data.find("LANGUAGE = Pcl") != -1))) :
            return 1
        else :    
            return 0
        
    def isPCLXL(self, data) :    
        """Returns 1 if data is PCLXL aka PCL6, else 0."""
        if ((data[:128].find("\033%-12345X") != -1) and \
             (data.find(" HP-PCL XL;") != -1) and \
             ((data.find("LANGUAGE=PCLXL") != -1) or \
              (data.find("LANGUAGE = PCLXL") != -1))) :
            return 1
        else :    
            return 0
            
    def detectPDLHandler(self) :    
        """Tries to autodetect the document format.
        
           Returns the correct PDL handler class or None if format is unknown
        """   
        # Try to detect file type by reading first block of datas    
        self.infile.seek(0)
        firstblock = self.infile.read(1024)
        self.infile.seek(0)
        if self.isPostScript(firstblock) :
            return PostScriptAnalyzer
        elif self.isPCLXL(firstblock) :    
            return PCLXLAnalyzer
        elif self.isPCL(firstblock) :    
            return PCLAnalyzer