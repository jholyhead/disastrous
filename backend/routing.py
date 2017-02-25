'''
Created on 7 Aug 2014

@author: fa1c12
'''
from py4j.java_gateway import JavaGateway
import json
import numpy as np
from position import Position
from position import convert2Cartesian, convert2LatLon

class Routing:
    
    routingService = None
    DISTANCE_PER_TICK = 0.0014
    MOVING_SPEED = 110 # meters per second
    
    def __init__(self, intervalLength = 1.0):
        if Routing.routingService == None:
            gateway = JavaGateway()
            Routing.routingService = gateway.entry_point.getRoutingService() 
        self.intervalLength = intervalLength
        #self.data = LoadOsm('foot')
        #self.router = Router(data)

    def route(self,startLat, startLong, endLat, endLong):
        '''
            Returns the route from {startLat,startLong} to {endLat,endLong}
            
            Returns a "json" object with two fields:
                route : contains a geoJson with the actual route
                timecoords : contains coordinates for each following timestep until the destination is reached
        '''
        routeInfo = Routing.routingService.getRoute(startLat,startLong,endLat,endLong);
        routeInfo = json.loads(routeInfo)
        geoJson = routeInfo['geoJson']
        coords = geoJson["coordinates"]
        time = 0
        timeCoords = [[time, startLat, startLong]]
        nextIndex = 1
        endLat, endLong = coords[len(coords)-1]
        lastLat,lastLon = startLat, startLong
        overallDistance = 0
        # while not arrived at end point
        while nextIndex < len(coords):
            #remainingDistance = Routing.DISTANCE_PER_TICK
            # set how far one can still travel during this tick
            remainingDistance = Routing.MOVING_SPEED * self.intervalLength
            
            #as long as remainingDistance has not been used up (or goal has been reached), do:
            while remainingDistance > 0 and nextIndex < len(coords):
                p1 = np.array([lastLat, lastLon])
                p2 = np.array(coords[nextIndex])
                
                p1 = convert2Cartesian(p1)
                p2 = convert2Cartesian(p2)
                
                v = (p2-p1)
                d = np.linalg.norm(v)
                
                if d > remainingDistance:
                    
                    overallDistance += remainingDistance
                    
                    p1 += (v * (remainingDistance/d))
                    time += int(self.intervalLength)
                    remainingDistance = 0
                    lastLat, lastLon = convert2LatLon(p1)
                    timeCoords.append([time, lastLat, lastLon])
                else:
                    
                    overallDistance += d
                    
                    lastLat, lastLon = coords[nextIndex]
                    nextIndex+=1
                    if nextIndex >= len(coords):
                        # arrived
                        time+=1
                        timeCoords.append([time, endLat, endLong])
                        #remainingDistance = 0
                    else:
                        if remainingDistance == d:
                            remainingDistance = 0
                            time += 1
                            timeCoords.append([time, lastLat, lastLon])
                        else:
                            remainingDistance -=d
        ret = {}
        ret["timecoords"] = timeCoords
        ret["route"] = geoJson
        ret["distance"] = overallDistance
        #ret = "{\n"
        #ret += '\t"timecoords": ' + str(timeCoords) + ',\n';
        #ret += '\t"route": \n'+geoJson + '\n}'
        return ret
    
    def advanceOnRoute(self, coordinates, intervals):
        remainingDistance = self.MOVING_SPEED * self.intervalLength * intervals
        lastLat, lastLon = coordinates[0]
        nextIndex = 1
        while remainingDistance > 0 and nextIndex < len(coordinates):
            p1 = np.array([lastLat, lastLon])
            p2 = np.array(coordinates[nextIndex])
            
            p1 = convert2Cartesian(p1)
            p2 = convert2Cartesian(p2)
            
            v = (p2-p1)
            d = np.linalg.norm(v)
            
            if d > remainingDistance:
                
                
                p1 += (v * (remainingDistance/d))
                remainingDistance = 0
                lastLat, lastLon = convert2LatLon(p1)
            else:
                
                
                lastLat, lastLon = coordinates[nextIndex]
                nextIndex+=1
                if remainingDistance == d:
                    remainingDistance = 0
                else:
                    remainingDistance -=d
        if nextIndex < len(coordinates):
            # normal case, something left
            newCoords = [[lastLat, lastLon]]
            newCoords.extend(coordinates[nextIndex:])
        elif remainingDistance > 0:
            # case of being in the last bit of the path
            newCoords = [[lastLat, lastLon], coordinates[nextIndex]]
        else:
            # arrived
            newCoords = []
        return newCoords

    def convertLatDistanceToMeters(self, lat1, lat2):
        pass
    
    def convertLongDistanceToMeters(self, lon1, lon2):
        pass
    
    def snapToRoad(self, lat, lon):
        lat,lon = Routing.routingService.getNearestPosition(lat, lon).split(",")
        lat = float(lat)
        lon = float(lon)
        return Position(lat, lon)
    
    
#r = Routing()
#route = r.route(52.455626, -1.935382, 52.444484, -1.917293)
