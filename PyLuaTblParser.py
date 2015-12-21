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

ERRORS = {
    'unexp_end_string': u'Unexpected end of string while parsing Lua string.',
    'unexp_end_table': u'Unexpected end of table while parsing Lua string.',
    'mfnumber_minus': u'Malformed number (no digits after initial minus).',
    'mfnumber_dec_point': u'Malformed number (no digits after decimal point).',
    'mfnumber_sci': u'Malformed number (bad scientific format).',
}

class MyParserException(Exception):pass

class PyLuaTblParser:
    """ to parse lua table constructors
    """
    def __init__(self):
        self.text = ''
        self.ch = ''
        self.at = 0
        self.len = 0
        self.depth = 0
        self.result = {}
        self.newline = '\n'
        self.tab = '\t'

    def load(self, s):
        if not s or type(s) is not str:
            return
        self.text = s
        self.removeComments()
        self.at = 0
        self.ch = ''
        self.depth = 0
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
                        backText += ' '
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
                elif state == B2: # block comment
                    if c == ']':
                        state = b1
                    else:
                        pass
                elif state == b1:
                    if c == ']':
                        state = S0
                        backText += ' '
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
        try:
            self.skip_white()
            if not self.ch:
                return
            if self.ch == '{':
                return self.object()
            if self.ch == "[":
                #if self.text[self.at] == '[':
                self.take_char()
                #     return self.string('[')
                # elif self.text[self.at] == '=':
                #     return self.string
                # else:
                #     self.take_char()
            if self.ch in ['"',  "'", '=']:
                return self.string(self.ch)
            elif self.ch.isdigit() or self.ch == '-':
                return self.number()
            else:
                return self.word()
        except MyParserException as e:
            print e
            return 0

    def skip_white(self):
        while self.ch:
            if self.ch in [' ', '\t', '\n', '\r']:
                self.take_char()
            else:
                break

    def take_char(self):
        if self.at < self.len:
            self.ch = self.text[self.at]
            self.at += 1
        else:
            self.ch = None

    def object(self):
        """
        an object is a dict or a list.
        :return:
        """
        myDi = {}
        myLi = []
        keyS = None
        self.take_char()
        self.skip_white()
        if self.ch and self.ch == '}': # exit, only when table is empty
            self.take_char()
            return myLi # so a list is proper rather than a dict
        else:
            while self.ch:
                self.skip_white()
                if self.ch == '{':
                    myLi.append(self.object())
                    continue
                elif self.ch == '}':
                    self.take_char()
                    if keyS is not None: # end with '}' without "'"
                        myLi.append(keyS) # must be a list item
                    if len(myDi) == 0: # if there is no A = B, myDi is empty, return list
                        return myLi
                    elif len(myLi) == 0: # else, return myDi.
                        myDi = {k:myDi[k] for k in myDi.keys() if myDi[k] is not None} # remove those None value.
                        return myDi
                    else: # merge dict and lst into one tbl
                        tblTemp = {x+1:myLi[x] for x in xrange(len(myLi))}
                        for k in myDi.keys():
                            if (k not in tblTemp.keys()) and (myDi[k] is not None):
                                tblTemp[k] = myDi[k]
                        myDi = {k:tblTemp[k] for k in tblTemp.keys() if tblTemp[k] is not None}
                        return myDi
                else: # not an object
                    if self.ch == ',':
                        self.take_char()
                        continue
                    else:
                        keyS = self.parse() # Now key is a string or a number
                        if self.ch == ']':
                            self.take_char()
                    self.skip_white()
                    ch = self.ch
                    if ch in ('=', ',', '}'):
                        if ch in ('=', ','):
                            self.take_char()
                        self.skip_white()
                        if ch == '=':
                            isDict = True
                            myDi[keyS] = self.parse()
                    else:
                        raise MyParserException
                        # else: # '}', end this obj without ","
                        #     myLi.append(keyS)
                        # keyS = None

                    # elif ch is not None and ch not in ['}']: # a word must be followed by = or ,
                    #     print 'This: ' + ch

    def string(self, quote):
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
    a2 = PyLuaTblParser()
    a3 = PyLuaTblParser()

    #test_str = '{array = {65,23,5,},dict = {mixed = {43,54.33,false,9,string = "value",},array = {3,6,4,},string = "value",},}'
    with open('test.txt') as f:
        test_str = f.read()

    a1.load(test_str)
    print 'a1.dict:'
    print a1.result

    print 'a1.dump:'
    print a1.dump()

    d1 = a1.dumpDict()
    print 'a1.dumpDict:'
    print d1

    a2.loadDict(d1)
    print 'loadDict(d1):'
    print a2.result

    a2.dumpLuaTable('f1.txt')
    a3.loadLuaTable('f1.txt')
    print 'a3.loadLuaTable:'
    print a3.result

    d3 = a3.dumpDict()
    print 'a3.dumpDict():'
    print d3
