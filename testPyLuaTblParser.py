import time
from PyLuaTblParser import PyLuaTblParser

a1 = PyLuaTblParser()
a2 = PyLuaTblParser()
a3 = PyLuaTblParser()

#test_str = '{array = {65,23,5,},dict = {mixed = {43,54.33,false,9,string = "value",},array = {3,6,4,},string = "value",},}'
f = open('test.txt')
test_str = f.read()
print test_str
f.close()

time.sleep(1)

print 'a1.dict:'
a1.load(test_str)
print a1.result


time.sleep(0.1)

print 'a1.dump:'
print a1.dump()
a1.load(a1.dump())

time.sleep(0.1)

print 'a1.dumpDict:'
d1 = a1.dumpDict()
print d1

time.sleep(0.1)

print 'loadDict(d1):'
a2.loadDict(d1)
print a2.result

time.sleep(0.1)

a2.dumpLuaTable('f1.txt')

time.sleep(0.1)

print 'a3.loadLuaTable:'
a3.loadLuaTable('f1.txt')
print a3.result

time.sleep(0.1)

print 'a3.dumpDict():'
d3 = a3.dumpDict()
print d3