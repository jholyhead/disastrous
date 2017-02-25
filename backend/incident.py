'''
Created on 6 Aug 2014

@author: fa1c12
'''
class Incident():
    
    def __init__(self, uid, incidentType, time, position):
        self.uid = uid
        self.incidentType = incidentType
        self.time = time
        self.pos = position
        self.children = []
        
    def addChild(self, child):
        self.children.append(child)
        return len(self.children)
        
    def childCount(self):
        return len(self.children)
    
