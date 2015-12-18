# coding=utf-8
# ginger
# - -
# 声明：本代码的解析过程参考了开源项目https://github.com/SirAnthony/slpp


S0 = 0
M1 = 1
M2 = 2
B1 = 3
B2 = 4
b1 = 5
S1 = 6


class MyParserException(Exception):pass


ERRORS = {
    'unexp_end_string': u'Unexpected end of string while parsing Lua string.',
    'unexp_end_table': u'Unexpected end of table while parsing Lua string.',
    'mfnumber_minus': u'Malformed number (no digits after initial minus).',
    'mfnumber_dec_point': u'Malformed number (no digits after decimal point).',
    'mfnumber_sci': u'Malformed number (bad scientific format).',
}

class PyLuaTblParser:
    """ to parse lua table constructors
    """
    def __init__(self):
        self.text = ''
        self.ch = ''
        self.at = 0
        self.len = 0
        self.depth = 0
        self.result = None
        self.newline = '\n'
        self.tab = '\t'

    def load(self, s):
        if not s or type(s) is not str:
            return
        self.text = s
        self.removeComments()
        self.at, self.ch, self.depth = 0, '', 0
        self.len = len(self.text)
        self.take_char()
        self.result = self.parse()

    def removeComments(self):
        """
        remove all the comments in query string
        :return:
        """
        state = S0
        lines = self.text.splitlines(True)
        backText = ""
        for line in lines:
            for c in line:
                if state == S0:
                    if c == '-':
                        state = M1
                    elif c == '\"':
                        state = S1
                        backText += c
                    else:
                        backText += c
                elif state == M1:
                    if c ==  '-': # line comments
                        state = M2
                    else:
                        state = S0
                        backText += '-' + c
                elif state == M2:
                    if c == '\n':
                        state = S0
                        backText += c
                    elif c == '[':
                        state = B1
                    else:
                        pass
                elif state == B1:
                    if c == '[':
                        state = B2
                    else:
                        state = M2
                elif state == B2:
                    if c == ']':
                        state = b1
                    else:
                        pass
                elif state == b1:
                    if c == ']':
                        state = S0
                    else:
                        state = B2
                elif state == S1:
                    if c == '\"':
                        state = S0
                        backText += c
                    else:
                        backText += c
        self.text = backText

    def parse(self):
        self.skip_white()
        if not self.ch:
            return
        elif self.ch == '{':
            return self.object()
        elif self.ch == "[":
            self.take_char()
        elif self.ch in ['"',  "'"]:
            return self.string(self.ch)
        elif self.ch.isdigit() or self.ch == '-':
            return self.number()
        else:
            return self.word()

    def skip_white(self):
        while self.ch:
            if self.ch in [' ', '\t', '\n', '\r']:
                self.take_char()
            else:
                break

    def take_char(self):
        if self.at >= self.len:
            self.ch = None
            return None
        self.ch = self.text[self.at]
        self.at += 1
        return True

    def object(self):
        tbl = {}
        lst = []
        keyN = 0
        keyS = None
        isDict = False
        self.depth += 1
        self.take_char()
        self.skip_white()
        if self.ch and self.ch == '}': #exit
            self.depth -= 1
            self.take_char()
            return tbl
        else:
            while self.ch:
                self.skip_white()
                if self.ch == '{':
                    res = self.object()
                    # TODO:ADD THIS RESULT INTO TABLE OR LIST
                    continue
                elif self.ch == '}':
                    self.depth -= 1
                    self.take_char()
                    if keyS is not None:# end with '}' without "'"
                        lst.append(keyS) # must be a list item
                    # if not numeric_keys and len([ key for key in o if type(key) in (str,  float,  bool,  tuple)]) == 0:
                    #     ar = []
                    #     for key in o:
                    #        ar.insert(key, o[key])
                    #     o = ar
                    # return o #or here
                    if len(tbl) == 0:
                        return lst
                    elif len(lst) == 0:
                        return tbl
                    else: # merge tbl
                        tblTemp = {x+1:lst[x] for x in xrange(len(lst))}
                        for k in tbl.keys():
                            if k not in tblTemp.keys():
                                tblTemp[k] = tbl[k]
                        tbl = tblTemp
                        return tbl
                else: # not an object
                    if self.ch == ',':
                        self.take_char()
                        continue
                    else:
                        keyS = self.parse() # Now key is a string or a number
                        #self.take_char()
                    self.skip_white()
                    ch = self.ch
                    if ch in ('=', ','):
                        self.take_char()
                        self.skip_white()
                        if ch == '=':
                            isDict = True
                            tbl[keyS] = self.parse()
                        else:
                            lst.append(keyS)
                        keyS = None

    def string(self, quote):
        # s = ''
        # start = self.ch
        #
        # if start in ['"',  "'"]:
        #     while self.take_char():
        #         if self.ch == quote:
        #             self.take_char()
        #             #if  self.ch == ']':
        #             return s
        #         if self.ch == '\\': # and start == end:
        #             self.take_char()
        #             if self.ch != end:
        #                 s += '\\'
        #         s += self.ch
        s = ''
        while self.take_char():
            if self.ch == quote:
                self.take_char()
                return s
            elif self.ch == '\\':
                self.take_char()
                if self.ch == quote:
                    s = s + '\\' + quote
            s += self.ch

    def number(self):
        def next_digit(err):
            n = self.ch
            self.take_char()
            if not self.ch or not self.ch.isdigit():
                raise MyParserException(err)
            return n
        n = ''
        try:
            if self.ch == '-':
                n += next_digit(ERRORS['mfnumber_minus'])
            n += self.take_digits()
            if n == '0' and self.ch in ['x', 'X']:
                n += self.ch
                self.take_char()
                n += self.take_hex()
            else:
                if self.ch and self.ch == '.':
                    n += next_digit(ERRORS['mfnumber_dec_point'])
                    n += self.take_digits()
                if self.ch and self.ch in ['e', 'E']:
                    n += self.ch
                    self.take_char()
                    if not self.ch or self.ch not in ('+', '-'):
                        raise MyParserException(ERRORS['mfnumber_sci'])
                    n += next_digit(ERRORS['mfnumber_sci'])
                    n += self.take_digits()
        except MyParserException as e:
            print e
            return 0
        try:
            return int(n, 0) # try to parse into integer with all base.
        except:
            pass
        return float(n)

    def take_digits(self):
        n = ''
        while self.ch and self.ch.isdigit():
            n += self.ch
            self.take_char()
        return n

    def take_hex(self):
        n = ''
        while self.ch and (self.ch in 'ABCDEFabcdef' or self.ch.isdigit()):
            n += self.ch
            self.take_char()
        return n

    def word(self):
        s = ''
        if self.ch != '\n':
          s = self.ch
        while self.take_char():
            if self.ch.isalnum():
                s += self.ch
            else:
                if s == 'true':
                    return True
                elif s == 'false':
                    return False
                elif s == 'nil':
                    return None
                else:
                    return str(s)

    def dump(self):
        return self.encode(self.result)

    def encode(self, obj):
        s = ''
        tab = self.tab
        newline = self.newline
        tp = type(obj)
        if tp is str:
            s += '"%s"' % obj.replace(r'"', r'\"')
        elif tp in [int, float, long, complex]:
            s += str(obj)
        elif tp is bool:
            s += str(obj).lower()
        elif tp in [list, tuple, dict]:
            self.depth += 1
            if len(obj) == 0 or ( tp is not dict and len(filter(
                    lambda x:  type(x) in (int,  float,  long) \
                    or (type(x) is str and len(x) < 10),  obj
                )) == len(obj) ):
                newline = tab = ''
            dp = tab * self.depth
            s += "%s{%s" % (tab * (self.depth - 2), newline)
            if tp is dict:
                s += (',%s' % newline).join(
                    [self.encode(v) if type(k) is int \
                        else dp + '%s = %s' % (k, self.encode(v)) \
                        for k, v in obj.iteritems()
                    ])
            else:
                s += (',%s' % newline).join(
                    [dp + self.encode(el) for el in obj])
            self.depth -= 1
            s += "%s%s}" % (newline, tab * self.depth)
        return s

    def loadLuaTable(self, f):
        try:
            fp = open(f, 'r')
            if not fp:
                raise MyParserException(u'Open file '+ f + u' failed\n')
            file_str = fp.read()
            self.load(file_str)
            fp.close()
        except MyParserException as e:
            print e

    def dumpLuaTable(self, f):
        try:
            fp = open(f, 'w')
            if not fp:
                raise MyParserException(u'Open file '+ f + u' failed\n')
            fp.write(self.dump())
            fp.close()
        except MyParserException as e:
            print e

    def loadDict(self, d):
        self.result = self.myLoadDict(d)

    def myLoadDict(self, obj):
        try:
            if type(obj) in [str, float, int, bool]:
                return obj
            elif type(obj) is list:
                tlist = []
                for i in obj:
                    tlist.append(self.myLoadDict(i))
                return tlist
            elif type(obj) is dict:
                tdict = {}
                for k in obj:
                    if type(k) in (float, int, str):
                        tdict[k] = self.myLoadDict(obj[k])
                return tdict
            else:
                raise MyParserException(u'loadDict type error\n')

        except MyParserException as e:
            print e

    def dumpDict(self):
        return  self.myLoadDict(self.result)




if __name__ == '__main__':
    a1 = PyLuaTblParser()
    s = '{array = {65,23,5,},dict = {mixed = {43,54.33,false,9,string = "value--asd",},--[[sd\n\nasd]]--\narray = {3,6,4,},string = "value",},}'
    #s = '{mixed = {43,false,string = "value--asd",}}'
    a1.load(s)
    print a1.text
    print a1.result

    print a1.dump()
