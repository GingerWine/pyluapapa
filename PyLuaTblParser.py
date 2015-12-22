# coding=utf-8
# ginger
# - -
# 声明：本代码的解析过程参考了开源项目https://github.com/SirAnthony/slpp


S0 = 0
M1 = 1
M2 = 2
M3 = 8
B1 = 3
B2 = 4
b1 = 5
S1 = 6
S2 = 7

SS1 = 9
SS2 = 10
SS3 = 11
SS4 = 12

class MyParserException(Exception):pass
class ParseNumberException(Exception):pass
class FileException(Exception):pass
class LoadDictTypeException(Exception):pass
class IllegalVarNameException(Exception):pass

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
        self.lf = '\n'
        self.tab = '\t'

    def load(self, s):
        if not s or type(s) is not str:
            return
        self.text = s
        self.removeComments()
        # print "RC:"
        # print self.text
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
        quote = ''
        for line in lines:
            for c in line:
                if state == S0:
                    if c == '-':
                        state = M1
                    elif c == '"' or c == "'":
                        quote = c
                        state = S1
                        backText += c
                    elif c == '[':
                        state = SS1
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
                        state = M3 # impossible to be block comment
                elif state == M3:
                    if c == '\n':
                        state = S0
                        backText += ' '
                        backText += c
                elif state == B1:
                    if c == '[':
                        state = B2
                    else:
                        state = M3
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
                    if c == quote:
                        state = S0
                        backText += c
                    elif c == '\\':
                        state = S2
                        backText += c
                    else:
                        backText += c
                elif state == S2:
                    state = S1
                    backText += c
                elif state == SS1:
                    if c == '[': # a [[ ]] string
                        state = SS2
                        backText += c
                    elif c == '"' or c == "'":
                        quote = c
                        state = S1
                        backText += c
                    elif c == '-':
                        state = M1
                    else:
                        state = S0
                        backText += c
                elif state == SS2:
                    if c == ']':
                        state = SS3
                        backText += c
                    else:
                        backText += c
                elif state == SS3:
                    if c == ']':
                        state = S0
                        backText += c
                    else:
                        state = SS2
                        backText += c

        self.text = backText

    def parse(self):
        self.skip_white()
        if not self.ch:
            return
        if self.ch == '{':
            return self.object()
        if self.ch == "[":

            self.take_char()
            self.skip_white()

        if self.ch in ['"',  "'", '[']:
            return self.string(self.ch)
        elif self.ch.isdigit() or self.ch in '-+.':
            return self.number2()
        else:
            return self.word()


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
            return True
        else:
            self.ch = None
            return False

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
                    myLi.append(self.parse())
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
                    keySIsWord = False
                    if self.ch in (',', ';'):
                        self.take_char()
                        continue
                    else:
                        keyS = self.parse() # Now key is a string or a number
                        if type(keyS) is tuple:
                            keyS = keyS[0]
                            keySIsWord = True
                        if self.ch == ']':
                            self.take_char()
                    self.skip_white()
                    ch = self.ch
                    if ch in ('=', ',', '}', ';'):
                        if ch in ('=', ',', ';'):
                            self.take_char()
                        self.skip_white()
                        if ch == '=':
                            myDi[keyS] = self.parse()
                            keyS = None
                        else: # is "," or "}"
                            if keySIsWord:
                                myLi.append(None)
                            else:
                                myLi.append(keyS)
                            keyS = None
                    else:
                        print "Error position : " + str(self.at) + ' ' + self.text[self.at-20:self.at-1]
                        raise MyParserException
                        # else: # '}', end this obj without ","
                        #     myLi.append(keyS)
                        # keyS = None

                    # elif ch is not None and ch not in ['}']: # a word must be followed by = or ,
                    #     print 'This: ' + ch

    def string(self, quote):
        s = ''
        if quote == '[':
            while self.take_char():
                if self.text[self.at-1:self.at+1] == ']]':
                    self.take_char()
                    self.take_char()
                    self.skip_white()
                    return s.decode("string_escape")
                else:
                    s += self.ch
        else:
            while self.take_char():
                if self.ch == quote:
                    self.take_char()
                    self.skip_white()
                    return s.decode("string_escape")

                elif self.ch == '\\':
                    self.take_char()
                    if self.ch == quote:
                        s += quote
                    else:
                        s += '\\' + self.ch
                else:
                    s += self.ch

    def number(self):
        n = ''
        try:
            if self.ch == '-':
                n += self.next_digit(ERRORS['mfnumber_minus'])
            n += self.take_digits()
            if n == '0' and self.ch in ['x', 'X']:
                n += self.ch
                self.take_char()
                n += self.take_hex()
            else:
                if self.ch and self.ch == '.':
                    n += self.next_digit(ERRORS['mfnumber_dec_point'])
                    n += self.take_digits()
                if self.ch and self.ch in ['e', 'E']:
                    n += self.ch
                    self.take_char()
                    if not self.ch or self.ch not in ('+', '-'):
                        raise MyParserException(ERRORS['mfnumber_sci'])
                    n += self.next_digit(ERRORS['mfnumber_sci'])
                    n += self.take_digits()
        except MyParserException as e:
            print e
            return 0
        try:
            return int(n, 0) # try to parse into integer with all base.
        except:
            pass
        return float(n)

    def number2(self):
        n = ''
        n += self.ch
        while self.take_char():
            if self.ch.isdigit() or self.ch in '-+eE.xXABCDEFabcdef':
                n += self.ch
            else:
                break
        try:
            self.skip_white()
            return eval(n)
        except: # yes, raise my own exception. capricious~
            raise ParseNumberException


    def next_digit(self, err):
        n = self.ch
        self.take_char()
        if not self.ch or not self.ch.isdigit():
            raise MyParserException(err)
        return n

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
        if self.ch.isalnum() or self.ch == '_':
            s += self.ch
        else:
            raise IllegalVarNameException
        while self.take_char():
            if self.ch.isalnum() or self.ch == '_':
                s += self.ch
            else:
                if s == 'true':
                    return True
                elif s == 'false':
                    return False
                elif s == 'nil':
                    return None
                else:
                    return (str(s), True)

    def dump(self):
        return self.my_encode(self.result, 0)

    def encode(self, obj):
        s = ''
        tab = self.tab
        newline = self.lf
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

    def my_encode(self, obj, dep):
        s = ''
        tp = type(obj)
        if tp is str:
            s +=  '"%s"' % obj.encode("string_escape").replace(r'"', r'\"') + ','
        elif tp in (int, long, float):
            s += str(obj) + ','
        elif tp is bool:
            s += str(obj).lower() + ','
        elif obj is None:
            s += 'nil' + ','
        elif tp in (list, dict):
            if tp is list:
                s += self.tab*0 + '{\n'
                for i in obj:
                    s += self.tab*(dep+1) + self.my_encode(i, dep+1) + self.lf
                s += self.tab*dep + '},\n'
            else:
                s += self.tab*0 + '{\n'
                for i in obj.keys():
                    s += self.tab*(dep+1) + self.my_encode_key(i) + ' = ' + self.my_encode(obj[i], dep+1) + self.lf
                s += self.tab*dep + '},\n'
        return s

    def my_encode_key(self, obj):
        s = ''
        tp = type(obj)
        if tp is str:
            #s +=  '"%s"' % obj.replace(r'"', r'\"')
            s +=  '["%s"]' % obj.encode("string_escape").replace(r'"', r'\"')
        elif tp in (int, long, float):
            s += '['+str(obj)+']'
        return s

    def loadLuaTable(self, f):
        fp = open(f, 'r')
        if not fp:
            raise FileException(u'Open file '+ f + u' failed\n')
        file_str = fp.read()
        self.load(file_str)
        fp.close()


    def dumpLuaTable(self, f):
        fp = open(f, 'w')
        if not fp:
            raise FileException(u'Open file '+ f + u' failed\n')
        fp.write(self.dump())
        fp.close()

    def loadDict(self, d):
        self.result = self.myLoadDict(d)

    def myLoadDict(self, obj):
        if type(obj) in [str, float, int, bool, long]:
            return obj
        elif obj is None:
            return obj
        elif type(obj) is list:
            tlist = []
            for i in obj:
                tlist.append(self.myLoadDict(i))
            return tlist
        elif type(obj) is dict:
            tdict = {}
            for k in obj:
                if type(k) in (float, int, str, long):
                    tdict[k] = self.myLoadDict(obj[k])
            return tdict
        else:
            raise LoadDictTypeException(u'loadDict type error\n')


    def dumpDict(self):
        return  self.myLoadDict(self.result)




if __name__ == '__main__':
    a1 = PyLuaTblParser()
    a2 = PyLuaTblParser()
    a3 = PyLuaTblParser()

    #test_str = '{array = {65,23,5,},dict = {mixed = {43,54.33,false,9,string = "value",},array = {3,6,4,},string = "value",},}'
    f = open('test.txt')
    test_str = f.read()
    print test_str
    f.close()

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
