#Copyright (c) 2010, Kitty Cooper, Open Sky Web Design
#       All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification, are permitted provided
# that the following conditions are met:
#
# 	1. Redistributions of source code must retain the
#	   above copyright notice, this list of conditions
#	   and the following disclaimer. 
#
#	2. Redistributions in binary form must reproduce the
#       above copyright notice, this list of conditions
#       and the following disclaimer in the documentation
#       and/or other materials provided with the
#       distribution. 
#
#	3. Neither the name of Kitty Cooper or the
#       names of its contributors may be used to endorse
#       or promote products derived from this software
#       without specific prior written permission. 
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

def processline(newline,indexvar):
    loopvar = "$" + indexvar
    newline= string.replace(newline,indexvar,loopvar)
    objitem = loopvar + "]."
    newobj = loopvar + "] ->"
    newline= string.replace(newline,objitem,newobj)
    return newline

def processcalls(command,newline,smartyfunctions):  
    temp = string.split(command,"|")
    newcmd = command
    if len(temp) > 1:
        words = string.split(temp[1],":")
        if smartyfunctions.has_key(words[0]):
            func = smartyfunctions[words[0]]
        else:
            func = words[0]
        newcmd =  func +  "(" + temp[0]
        if len(words) > 1:
            for i in range(1,len(words)):
                newcmd = newcmd + "," + words[i]

        newcmd = newcmd  + ")"

    return newcmd
    
if __name__ == "__main__":

    import os, string, win32ui, win32con
    debug = 0

# list of samrty to php function conversions
#    
    smartyfunctions = { "replace" : "str_replace",
                      "capitalize" : "ucfirst",
                      "@count" : "count",
                      "count_characters" : "strlen",
                      "date_format":"strftime",
                      "lower":"strtolower",
                      "upper":"strtoupper"

                    }                    

  # cat is a +
                      
# use windows open file dialogue to get directory
#enclose entire report process in one big try

    print "Program to take a smarty template file and do a first cut at PHP conversion"
    print "    ... it will convert if, else, replace variables, sections with loops,"
    print "    ... some calls like replace but not fancier code"
    print "    ... and it will flag smarty lines it cannot convert with ##convert?## "
 
    flags=win32con.OFN_FILEMUSTEXIST
    ext = "tpl"
    filter = "Files of requested type (*%s)|*%s||" % (ext,ext)
    fileName = "default.tpl"
    d=win32ui.CreateFileDialog(1,None,fileName,flags,filter,None)
    d.DoModal()
    inputpath=d.GetPathName()
    print "path is",inputpath
    inputsplit=string.split(inputpath,"\\")
    inputdir = string.join(inputsplit[:-1],"\\")
    chkdir = string.join(inputsplit[:-1],"\\") + "\\"
    inputname=d.GetFileName()
    print "input file is ",inputname
    try:
        input = open(inputname,"r")   # expects text to mark up in input.txten
    except:
        if inputname:
            print "Invalid Input File ",inputname
            line = raw_input()
        sys.exit(2)
    #
    outname = string.replace(inputname,".tpl",".php")
    print "The output filename will be ",inputdir,outname
 
    try:
        output = open(outname,"w")
    except:
         print "Could not open output file ",outname
 
         print "Type return when ready to exit"
         line = raw_input()
         output.close()
         input.close()
         logfile.close()
         sys.exit(2) 
 
    inline = input.readline()

    start = "<?php echo "
    start2 = "<?php "
    end = "; ?>"
    end2 =" ?>\n"
    loopvar = ""
    while inline:
        newline = string.strip(inline)
        if newline and newline <>"\n":
            inline = " " + inline
            if string.find(inline,"{") > 0:
                tokens = string.split(inline,"{")
                before=1
                newline = ""
                for token in tokens:
                    if debug:
                        print "token is",token,
                        if before:
                            print "not a command"
                    if before:
                        newline = newline + token
                        before = 0
                    else:
                        token = string.strip(token)
                        newtokens = string.split(token,"}")
                        command = string.strip(newtokens[0])
                        if debug:
                            print "command is ",command," 2:",command[0:2]," 5:",command[0:6]
                        if command[0] == "$":
                            if debug:
                                print "first char is $"
                            if string.find(command,"|") > 1:
                                newline = newline + start2
                                newline = newline + processcalls(command,newline,smartyfunctions) + end
                                
                            else:    
                                newline = newline + start + command + end
                            if loopvar:
                                newline = processline(newline,indexvar)
                        elif command[0:2] == "if":
                            # is div by
                            loopon = "$smarty.section." + indexvar + ".rownum"
                            temp = command[2:]
                            temp = string.replace(temp,loopon,loopvar)
                            if string.find(temp,"is div by") > 1:
                                temp = string.replace(temp,"(","")
                                temp = string.replace(temp,")","")
                                words = string.split(temp)
                                temp =  "(" + words[4] + "%" + words[0] + ") == 0"
                            newline = newline + start2 + "if (" + temp + ") { " + end2
                        elif command == "else":
                            newline = newline + start2 + " \n} else { " + end2
                        elif command == "/if":
                            newline = newline + start2 + " \n} " + end2
                        elif command[0:6] == "assign":
                            if debug:
                                print "doing an assign, newline is",newline
                            if loopvar:
                                newline = processline(newline,indexvar)
                                if debug:
                                    print "checked for loppvar ",loopvar," line is ",newline
                            pos1 = string.find(command,"var")
                            pos2 = string.find(command," ",pos1)
                            newline = newline + start2 + "$" + command[pos1+5:pos2-1]
                            if debug:
                                print "doing an assign, newline is",newline
                            pos3 = string.find(command,"=",pos2)
                            temp = command[pos3+1:]
                            if string.find(temp,"|") > 1:
                                temp = processcalls(temp,newline,smartyfunctions)
                            newline = newline + " = " + temp + end
                        elif command[0:7] == "section":
                            # {section name=numloop loop=$list}
                            # becomes foreach ( $list as $numloop )
                            if debug:
                                print "doing section, newline is",newline
                            words = string.split(command[8:]," ")
                            for word in words:
                                varab= string.split(word,"=")
                                if varab[0]== "name":
                                    indexvar= varab[1]
                                    loopvar= "$" + indexvar
                                elif varab[0]== "loop":
                                    arrname = varab[1]
                            newline = start2 + "for (" + loopvar + "=0;" + loopvar + " < count(" 
                            newline = newline + arrname + "); " + loopvar + " ++) { " + end2
                            if debug:
                                print "doing section", newline

                        elif command == "/section":
                            newline = newline + " \n} // end of foreach\n" + end2
                            loopvar = ""
                          
                        else:
                            newline = newline + "##convert?## "  + command
                            
                        if len(newtokens) > 1:
                            newtokens[0] = ""
                            for newtoken in newtokens:
                                newline = newline + newtoken
                        newline = newline + "\n"
                        newline = string.replace(newline,"$$","$")
                        if loopvar:
                            temp = "$smarty.section." + indexvar +".rownum"
                            #print temp
                            newline = string.replace(newline,temp,loopvar)
                output.write(newline)
            else:
                output.write(inline)
        inline = input.readline()

        
    output.write("\n?>\n")
    input.close()
    output.close()
            
            






