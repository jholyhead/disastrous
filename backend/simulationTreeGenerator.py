'''
Created on 6 Aug 2014

@author: Frederik
'''
import numpy as np
from incident import Incident
from position import Position
from routing import Routing,  convert2Cartesian, convert2LatLon
import math
import hashlib
from python_image_code_v0_61.random_distributions import Distribution2D, distribution_from_grid
from python_image_code_v0_61.enhanced_grid import Grid2D

TYPE_FIRE = "fire"
TYPE_INJURY = "injury"
TYPE_LOOTERS = "looters"
INITIAL_INCIDENTS = 6

class SimulationTreeGenerator():
    
    def __init__(self, seed=1, timespan=100, maxChildren=1, minLat=52.455158, minLong=-1.949639, maxLat=52.444748, maxLong=-1.921165, initialFires=3, initialInjuries=3, initialLooters=3):
        self.seed = seed
        self.timespan = timespan
        self.maxChildren = maxChildren
        self.minPos = Position(minLat,minLong)
        self.maxPos = Position(maxLat,maxLong)
        grid = Grid2D((1, 1))
        grid[..., ...] = [[1]]
        probs = distribution_from_grid(grid, 1, 1)
        self.distribution = Distribution2D(probs, convert2Cartesian(np.array([minLat, minLong])), convert2Cartesian(np.array([maxLat, maxLong])))
        
        self.initialFires = initialFires
        self.initialInjuries = initialInjuries
        self.initialLooters = initialLooters
        
        self.incidentProximity = 100
        self.spreadProximity = 200
        
        self.fireProbability = 0.055
        self.injuryProbability = 0.06
        self.looterProbability = 0.055
        
        self.fireSpreadChance = 0.015
        self.looterSpreadChance = 0.005
                
        self.id = 0
        np.random.seed(self.seed)
        
    def hash(self):
        h = hashlib.md5()
        h.update(str(self.seed))
        h.update(str(self.timespan))
        h.update(str(self.maxChildren))
        h.update(str(self.minPos))
        h.update(str(self.maxPos))
        h.update(str(self.initialFires))
        h.update(str(self.initialInjuries))
        h.update(str(self.initialLooters))
        h.update(str(self.incidentProximity))
        h.update(str(self.spreadProximity))
        h.update(str(self.fireProbability))
        h.update(str(self.injuryProbability))
        h.update(str(self.looterProbability))
        h.update(str(self.fireSpreadChance))
        h.update(str(self.looterSpreadChance))
        return h.hexdigest()

    def simulate(self):
        np.random.seed(self.seed)
        steps = [1 for _ in range(self.timespan*2)]
        fireSpawns = np.random.binomial(steps,self.fireProbability)
        injurySpawns = np.random.binomial(steps, self.injuryProbability)
        looterSpawns = np.random.binomial(steps, self.looterProbability)
        tree = []
        self.id = 0
        
        # have some initial incidents
        for _ in range(self.initialFires):
                incident = Incident(self.id, TYPE_FIRE, 0, self.getRandomPositionRestricted(tree, self.checkProximity, tries = 1000000))
                self.id += 1
                tree.append(incident)
        for _ in range(self.initialInjuries):
                incident = Incident(self.id, TYPE_INJURY, 0, self.getRandomPositionRestricted(tree, self.checkProximity, tries = 1000000))
                self.id += 1
                tree.append(incident)
        for _ in range(self.initialLooters):
                incident = Incident(self.id, TYPE_LOOTERS, 0, self.getRandomPositionRestricted(tree, self.checkProximity, tries = 1000000))
                self.id +=1
                tree.append(incident)
                
        for i in range(self.timespan*2):
            if fireSpawns[i]:
                pos = self.getRandomPositionRestricted(tree, self.checkProximity)
                if(pos != False):
                    incident = Incident(self.id, TYPE_FIRE, i, pos)
                    self.id += 1
                    tree.append(incident)
            if injurySpawns[i]:
                pos = self.getRandomPositionRestricted(tree, self.checkProximity)
                if(pos != False):
                    incident = Incident(self.id, TYPE_INJURY, i, pos)
                    self.id += 1
                    tree.append(incident)
            if looterSpawns[i]:
                pos = self.getRandomPositionRestricted(tree, self.checkProximity)
                if(pos != False):
                    incident = Incident(self.id, TYPE_LOOTERS, i, pos)
                    self.id += 1
                    tree.append(incident)
        treeMaxIndex = len(tree)
        for inc in tree:
            self.inflateNode(inc, tree)
        return tree[0:treeMaxIndex]
                
    def getRandomPosition(self):
        lat, lon = convert2LatLon(self.distribution(np.random.uniform(), np.random.uniform()))
        r = Routing()
        return r.snapToRoad(lat, lon)
        
    def checkProximity(self, loc, incidents, incident = None):
        for inc in incidents:
            if(inc.pos.distanceFrom(loc) < self.incidentProximity):
                return False
        return True
        
    def checkNearProximity(self, loc, incidents, incident):
        if(incident.pos.distanceFrom(loc) > self.spreadProximity):
            return False
        if(not self.checkProximity(loc, incidents)):
            return False
        return True
    
#    def getRandomPositionNearOther(self,position, spreadArea, adjust = True):
#        lat = np.random.normal(position.lat,spreadArea)
#        if lat< self.minPos.lat:
#            lat = self.minPos.lat
#        elif lat > self.maxPos.lat:
#            lat = self.maxPos.lat
#            
#        lon = np.random.normal(position.lon,spreadArea)
#        if lon < self.minPos.lon:
#            lon = self.minPos.lon
#        elif lon > self.maxPos.lon:
#            lon = self.maxPos.lon
#            
#        r = Routing()
#        #print "near another: " + str((lat, lon))
#        return r.snapToRoad(lat, lon)
    
    def getRandomPositionRestricted(self, incidents, checkFcn, parent = None, tries = 1000):
        for _ in range(tries):
            pos = self.getRandomPosition()
            if(checkFcn(pos, incidents, parent)):
                break
            pos = False
        return pos
    
    def inflateNode(self, incident, incidents):
        currentTime = incident.time
        if incident.incidentType == TYPE_FIRE:
            prob = self.fireSpreadChance
        elif incident.incidentType == TYPE_LOOTERS:
            prob = self.looterSpreadChance
        else:
            prob = 0
            
        if prob == 0:
            pass
        
        while currentTime < self.timespan and incident.childCount() < self.maxChildren:
            currentTime += 1
            if np.random.binomial([1],prob):
                pos = self.getRandomPositionRestricted(incidents, self.checkNearProximity, incident)
                if(pos != False):
                    child = Incident(self.id, incident.incidentType, currentTime, pos)
                    self.id +=1
                    incidents.append(child)
                    incident.addChild(child)
                    self.inflateNode(child, incidents)
        
#handler = SimulationTreeGenerator(1, 100, 2, 0, 0, 1, 1)
#print json.dumps(handler.simulate(), default=lambda o: o.__dict__,sort_keys=True, indent=2)
#print json.dumps(handler.simulate().__dict__)
    
#events = np.random.binomial([1 for x in range(100)],0.2)
#c = 0
#for e in events:
#    if e:
#        c += 1
#        
#print c/float(len(events))