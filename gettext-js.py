# encoding=UTF8
import re
import os

#
# gettext-js - a hack to get translation strings from JavaScript files
# 
# Copyright (C) 2011 Borgar Thorsteinsson
# Licensed under the terms of the MIT software license.
#
# This is a naiive hack to produce gettext compatible files from JavaScript.
# xgettext doesn't have support for the JavaScript language and the de-facto
# way of doing things seems to be applying some nasty regular expressions on
# the JS file and running it through xgettext as either Python or Perl.
#
# I have found this method to be insufficent for the code I write. Thus, this
# nasty thing. Theoretically, it is just as crappy as the other way. However 
# in practice it wins out because it is better maintainable, smaller, and
# runs as a pure-Python solution (a plus if that is your environment).
#


output_head = """# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2011-12-22 22:15+0000\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=CHARSET\\n"
"Content-Transfer-Encoding: 8bit\\n"
"""

# TODO: pick these up from command line and add to the regexp runtime.
# TODO: we need to be able to add a number to these specifying how many strings they are allowed to pick up.
# patterns = [ '_', 'getText', 'ngetText' ]

re_str = re.compile(r"""
        (?:
          (?P<string_double>
            "[^\n]*?(?<!\\)"
          )
          |
          (?P<string_single>
            '[^\n]*?(?<!\\)'
          )
          |
          (?P<comment_block>
             /\* (?: [\s\S]*? ) \*/
          )
          |
          (?P<comment_line>
             //[^\n]+
          )
          |
          (?P<regexp>
             (?<![\w$\)\]<>])
             / (?: \\/ | [^\n/] )+ /
             (?!/)[gim]*
          )
          |
          (?P<translatable>
            (?<![\w$])  # any space or operator 
            (?P<pattern> _ | getText | ngetText )  # translation function
            \(
            [\s\n]* # ws* 
            (
                "(\\"|[^"\n]+)*"
                |
                '(\\'|[^'\n]+)*'
            )
            # there is no terminator here as we do more parsing if we hit this
          )
        )
        # whatever else ...
        """, re.X)


def gettext( filename ):

    js = open( filename, 'r' ).read();
    # force unicode here

    # create an offset-to-line map
    line = 1
    br = range( 0, len(js) )
    for i,c in enumerate(js):
        if c == '\n': line += 1
        br[ i ] = line

    # match repo
    matchorder = []
    matches = {}

    pos = 0
    c = 0
    while True:
        # matches comment or regexp
        chunk = re_str.search( js, pos )
        if chunk:
            if chunk.group('translatable'):
                # the basic idea here is that until we find the end of the function
                # we concatinate strings as we find them. When we hit something that
                # isn't a string or allowed operator (paren, comma, plus) we stop adding
                # texts.
                #
                # _( "" )
                # _( "", "", lang )
                # _( ("") + "", lang )
                # _( "" + "", (lang + lang) )
                s = 0
                p = chunk.start() + len(chunk.group('pattern'))
                linenr = br[ chunk.start() ]
                instring = False
                strings = ['']
                locked = False
                num_allowed_strings = 2 if chunk.group('pattern') == 'ngetText' else 1
                while p < len(js):
                    c = js[ p ]
                    if instring:
                        if c == instring and not js[ p-1 ] == '\\':
                            instring = False
                        elif c == instring and js[ p-1 ] == '\\':
                            if not locked:
                                strings[-1] = strings[-1][:-1] + c
                        else:
                            if not locked:
                                strings[-1] = strings[-1] + c
                    else:
                        if c in ( '"', "'" ):
                            instring = c
                        elif c == '(':
                            s += 1
                        elif c == ')':
                            s -= 1
                            if not s: break # found end
                        elif c == ',':
                            if num_allowed_strings < len(strings):
                                strings.append( '' )
                            else:
                                locked = True
                        elif c in ( '+', '\n', '\t', '\r', ' ' ):
                            # ignore whitespace
                            pass
                        else:
                            locked = True

                    p += 1
                    if p > chunk.end() + 200:
                        # FIXME: we should really issue a warning here
                        raise Exception( 'Parse error in line %s' % linenr )
                        # raise SyntaxError('Something has done wrong in %s line %s', (filename, linenr))
                        #p = chunk.end() # this is really a bad way to be robust
                        #break                    

                for string in strings:
                    if string in matches:
                        md = matches[ string ]
                        md['lines'].append( linenr )
                    else:
                        matchorder.append( string )
                        matches[ string ] = {
                            'id': string,
                            'lines': [ linenr ]
                        }

                pos = p
            else:
                # this is (hopefully) an ignorable chunk
                pos = chunk.end()
        else:
            break
    
    def esc(s):
        return s.replace('\"','\\"').replace('\n','\\n')

    # format results
    absfile = os.path.abspath( filename )
    out = output_head.split('\n')
    for msgid in matchorder:
        msg = matches[ msgid ]
        for line in msg['lines']:
            out.append( "#: %s:%s" % (absfile, line) )
        # fixme: deal with flags: ", javascript-format"
        e = esc(msgid)
        if len( e ) < 75:
            out.append( "msgid \"%s\"" % e )
        else:
            out.append( "msgid \"\"" )
            # chunk string into 75 char lines
            s = ''
            for b in re.split(ur'(\s)', e):
                if len(s) + len(b) < 74:
                    s = s + b
                else:
                    out.append( '"%s"' % s )
                    s = b
            if s: out.append( '"%s"' % s )
        out.append( 'msgstr ""\n' )
    return "\n".join(out)



if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        sys.exit('Usage: %s javascript-file' % sys.argv[0])

    print gettext( sys.argv[1] )

