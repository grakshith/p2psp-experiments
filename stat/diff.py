#! /usr/bin/env python
import sys
f1 = open('1.hex','r')
f2 = open('2.hex','r')
s=f1.read()
s2 = f2.read()
print(len(s))
print(len(s2))
#print s2
strlen =  int(sys.argv[1])
c=s.find(s2[:+strlen])
print(s2[:+strlen])
print str(c/1024)+" chunks "+str(c%1024)+"bytes"  
s3=s[c:c+1024]
#print s3
#print s2[:1024]
print(s3==s2[:1024])
