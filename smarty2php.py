import sys
import string
import os.path
import re

# global vars 
DEBUG = 1
# need to keep track of loopvar between translations, 
# but translate is used as a callback. so it's global
INDEX = ''
FIXME = '<? /* FIXME: smarty-translation'

def processloopvar(str):
    return str.replace(INDEX,'$' + INDEX)

def propfilter(str):
    # note: this results in nested arrays looking like function calls :\
    # there's no good way to tell the difference.
    return str.replace('].', ']->')

def arrayfilter(str):
    return re.sub(r'\.(\d+)', '[\g<1>]', str)

def processcall(command):  
    # list of smarty to php function conversions
    smartyfunctions = { 'replace' : 'str_replace',
                      'capitalize' : 'ucfirst',
                      '@count' : 'count',
                      'count_characters' : 'strlen',
                      'date_format':'strftime',
                      'lower':'strtolower',
                      'upper':'strtoupper'
                    }                    
    temp = string.split(command,'|')
    newcmd = command
    if len(temp) > 1:
        words = string.split(temp[1],':')
        if smartyfunctions.has_key(words[0]):
            func = smartyfunctions[words[0]]
        else:
            func = words[0]
        newcmd =  func +  '(' + temp[0]
        if len(words) > 1:
            for i in range(1,len(words)):
                newcmd = newcmd + ',' + words[i]

        newcmd = newcmd  + ')'

    return newcmd

def translate(match):
    # trim off the braces
    stuff = match.group(0)
    stuff = stuff[1:len(stuff)-1]

    global INDEX
    block = False
    open = '<?'
    close = '?>'
    ret_str = ''

    if stuff[0] == '$':
        if stuff.find('|') > 1:
            ret_str = open + processcall(stuff) + ';' + close
        else:
            ret_str = open + '=' + stuff + ';' + close
        if INDEX:
            ret_str = processloopvar(ret_str)
    elif stuff[:2] == 'if':
        # is div by
        cond = stuff[2:]
        if cond.find('is div by') > 1:
            cond = cond.replace('(','')
            cond = cond.replace(')','')
            words = cond.split()
            cond =  '(' + words[4] + '%' + words[0] + ') == 0'
        ret_str = ret_str + open + ' if (' + cond.strip() + '): ' + close
    elif stuff == 'else':
        ret_str = ret_str + open + ' else: ' + close
    elif stuff == '/if':
        ret_str = ret_str + open + ' endif; ' + close
    elif stuff == 'literal' or stuff == '/literal':
        # just let it go away
        pass
    elif stuff[:6] == 'assign':
        # {assign var="name" value="Bob"}
        # becomes
        # <? $name = "Bob"; ?>
        if INDEX:
            ret_str = processloopvar(ret_str)
#            if DEBUG:
#                print 'checked for loopvar %s; line is %s' % (INDEX, ret_str)
        # there may or may not be spaces around the '='s
        words = stuff.split()
        for token in words[1:]:
            if token.find('=') >= 0:
                tup = token.strip().split('=')
                if tup[0] == 'var':
                    var = tup[1].strip()
                elif tup[0] == 'value':
                    val = tup[1].strip()
                    if val.find('|') > 0:
                        val = processcall(val)
        if var and val:
            ret_str = '%s $%s = %s; %s' % (open, var, val, close)
        else:
            ret_str = '%s failure: %s */ ?>' % (FIXME, stuff)

    elif stuff[:7] == 'section':
        # {section name=numloop loop=$list}
        # becomes for ($name=0; $name < $loop; $name++)
        stuff = stuff.split()
        ret_str = ''
        for word in stuff[1:]:
            token = word.split('=')
            if token[0] == 'name':
                INDEX = token[1]
                if DEBUG:
                    print 'found loop index variable is %s' % INDEX
            elif token[0]== 'loop':
                # this may be a number, var or an array
                loop = token[1]
                # there is no easy way to tell btwn var and array :\
                ret_str += '%s: if %s was an int delete \'count\' */ ?>' % (FIXME, loop)
                try: 
                    int(loop)
                except ValueError:
                    loop = 'count(%s)' % loop
        ret_str += '%s for ($%s=0; $%s<%s; %s++): %s' % (open, 
                                INDEX, INDEX, loop, INDEX, close)
    elif stuff == '/section':
        ret_str = '%s endfor; %s' % (open, close)
        INDEX = ''

    elif stuff[:9] == 'translate':
        trash, text = stuff.split('=')
        text = re.sub('"', '\'', text)
        ret_str = '%s=$this->transEsc(%s) %s' % (open, text, close)

    else:
        ret_str = '%s: did not convert %s */ ?>' % (FIXME, stuff)
        block = True

    if not block:
        if INDEX:
            temp = 'smarty.section.' + INDEX +'.index'
            ret_str = ret_str.replace(temp,INDEX)
        ret_str = arrayfilter(ret_str)
        ret_str = propfilter(ret_str)

    if DEBUG: 
        print 'Stuff: %s' % stuff
        print 'Returning: %s' % ret_str
    return ret_str


def main(infile):
    # check for good input file
    if not os.path.exists(infile):
        print 'File given does not exist: %s' % infile
        sys.exit(2)
    if not os.path.isfile(infile):
        print 'File given is not a file: %s' % infile
        sys.exit(2)
    base = os.path.basename(infile)
    inname, ext = base.split('.')
    if ext != 'tpl':
        print 'File given is not a .tpl file: %s' % infile
        sys.exit(2)

    # open output file
    outname = inname + '.phtml'
    print 'The output filename will be %s' % outname
    try:
        output = open(outname,'w')
    except:
         print 'Could not open output file %s' % outname
         input.close()
         sys.exit(2) 

    lcomment = re.compile('{\*')
    rcomment = re.compile('\*}')
    # note the ? makes it non-greedy
    smarty_pattern = re.compile('({\S.*?\S})')
    with open(infile, 'r') as input:
        for line in input:
            # replace all comments (may be multi-line)
            line = lcomment.sub('<? /*', line)
            line = rcomment.sub('*/ ?>', line)
            # translate any remaining smarty code
            line = smarty_pattern.sub(translate, line)
#            print line
            output.write(line)
    output.close()
            
if __name__ == '__main__':
    # require an arg
    if len(sys.argv) != 2:
        print 'One argument required; received %s' % str(len(sys.argv) - 1)
        sys.exit(2)
    main(sys.argv[1]);


