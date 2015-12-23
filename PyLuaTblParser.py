# coding=utf-8
# Author: ginger
# - -
# 声明：本代码的解析过程参考了开源项目https://github.com/SirAnthony/slpp


# State names below. For remove comments
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
        self.result = {}
        self.lf = '\n'
        self.tab = '\t'

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
            return self.my_object()
        if self.ch == "[":
            self.take_char()
            self.skip_white() # in square brackets, there may be BLANK characters
        if self.ch in ['"',  "'", '[']: # TODO: '[['type string is assumed not to be keys, but CAN be.
            return self.string(self.ch)
        elif self.ch.isdigit() or self.ch in '-+.':
            return self.my_number()
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

    def my_object(self):
        myLi = []
        myDi = {}
        keyS = None
        self.take_char()
        self.skip_white()
        if self.ch == '}': # Empty table
            self.take_char()
            return []
        while self.ch is not None:
            if self.ch == '{': # New table, must be a list item here
                myLi.append(self.my_object())
                continue
            elif self.ch == '}': # end of this object.
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
            #else: # normal item
            elif self.ch in ";,": # one item finished
                self.take_char()
                self.skip_white()
                continue
            else:
                keyS = self.parse()
                self.skip_white()
                if self.ch == ']':
                    self.take_char()
                    self.skip_white()
                ch = self.ch
                if ch in ",;}": # list item
                    if type(keyS) is tuple:
                        keyS = None
                    myLi.append(keyS)
                    keyS = None
                    if ch in ",;":
                        self.take_char()
                        self.skip_white()
                elif ch == '=': # dict key
                    if type(keyS) is tuple:
                        keyS = keyS[0]
                    self.take_char()
                    self.skip_white()
                    myDi[keyS] = self.parse()
                    keyS = None
                    self.skip_white()
                else:
                    raise MyParserException





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

    def my_number(self):
        '''
        eval() is a very useful function to parse numbers
        :return:
        '''
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
            s +=  '["%s"]' % obj.encode("string_escape").replace(r'"', r'\"')
        elif tp in (int, long, float):
            s += '['+str(obj)+']'
        return s

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

    def load(self, s):
        if not s or type(s) is not str:
            return
        self.text = s
        self.removeComments()
        self.at = 0
        self.ch = ''
        self.len = len(self.text)
        self.take_char()
        self.result = self.parse()

    def dump(self):
        return self.my_encode(self.result, 0)

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

    def dumpDict(self):
        return  self.myLoadDict(self.result)



if __name__ == '__main__':
    a1 = PyLuaTblParser()
    a2 = PyLuaTblParser()
    a3 = PyLuaTblParser()

    f = open('test.txt')
    test_str = f.read()
    f.close()

    a1.load(test_str)

    print a1.dump()

    d1 = a1.dumpDict()

    a2.loadDict(d1)

    a2.dumpLuaTable('f1.txt')
    a3.loadLuaTable('f1.txt')

    d3 = a3.dumpDict()

