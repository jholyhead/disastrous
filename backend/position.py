'''
Created on 26 Aug 2014

@author: fa1c12
'''

import numpy as np

class BirminghamConverter:
    def __init__(self):
        y_len = 2932
        y_diff = -1.918572210041825 + 1.8754203758672
        x_len = 3087
        x_diff = 52.49422011584404 - 52.46648021977516
        self.origo = np.array([52.47458031448539, -1.898368820794689])
        self.scale = np.array([x_len/x_diff, y_len/y_diff])    
    
def convert2Cartesian(p):
    b=BirminghamConverter()
    if(isinstance(p, Position)):
        p=p.toArray()
    return np.multiply(np.array(p)-b.origo, b.scale)

def convert2LatLon(p):
    b=BirminghamConverter()
    return np.divide(np.array(p), b.scale)+b.origo

class Position:
    
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        
    def __str__(self):
        return "["+str(self.lat)+", " + str(self.lon)+"]"
    
    def __repr__(self):
        return self.__str__()
        
    def toArray(self):
        return [self.lat, self.lon]
        
    def distanceFrom(self, other):
        if(isinstance(other, Position)):
            other=other.toArray()
        dv = convert2Cartesian(self.toArray()) - convert2Cartesian(other);
        return np.linalg.norm(dv)
        