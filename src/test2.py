'''
Created on Mar 16, 2011

@author: cgueret
'''
from Resources import Museum, Painting

if __name__ == '__main__':
    #a = Museum('altesnational')
    #print a.to_rdfxml()
    b = Painting('altesnational/woman-at-a-window')
    print b.to_rdfxml()