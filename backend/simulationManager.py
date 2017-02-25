'''
Created on 26 Aug 2014

@author: fa1c12
'''

import routing
import copy
import threading
import math
import time
import os
import json
from __builtin__ import Exception
from simulationTreeGenerator import SimulationTreeGenerator
from position import Position
from simulationRunner import SimulationRunner
from routing import Routing
from incident import Incident

DEBUG = False
SCOREBOARD_FOLDER = 'scoreboards'
STORED_TREES_FOLDER = 'stored_trees'
AGENT_ACTIONS_FOLDER = 'agent_actions'
LOG_FOLDER = 'logs'

def getScoreboardFileForToday():
    if not os.path.exists(SCOREBOARD_FOLDER):
        os.makedirs(SCOREBOARD_FOLDER)
    return SCOREBOARD_FOLDER + "/" +time.strftime("%Y-%m-%d") + "_scores.csv"

class SimulationState:
    
    def __init__(self,userId, timespan, eventTree, fireFighters, officers, ambulances, logfolder = False):
        self.userId = userId
        self.uidString = ("[userId=" + str(userId)+"]").ljust(13)
        self.t = 0
        self.maxChildCount = 0
        for incident in eventTree:
            self.maxChildCount += self.countChildren(incident)
        self.currentScore = 0
        self.timespan = timespan
        self.eventTree = eventTree
        self.activeIncidents = []
        self.resolvedIncidentIds = []
        self.fireFighters = {}
        self.officers = {}
        self.ambulances = {}
        self.simulationHash = None
        self.logfolder = logfolder
        if self.logfolder:
            logId=1
            if not os.path.exists(self.logfolder):
                os.mkdir(self.logfolder)
            while os.path.isfile(self.logfolder+"/"+str(logId)):
                logId+=1
            self.logfolder = self.logfolder+"/"+str(logId)
        for k,v in fireFighters.iteritems():
            self.fireFighters[k] = {"pos": copy.deepcopy(v), "path":None, "route": [[v.lat, v.lon]], "incidentId": None}
            self.log(self.t, "init",{"responderId": k, "pos": v, "type":"fireFighter"})
        for k,v in officers.iteritems():
            self.officers[k] = {"pos": copy.deepcopy(v), "path":None, "route": [[v.lat, v.lon]], "incidentId": None}
            self.log(self.t, "init",{"responderId": k, "pos": v, "type":"officer"})
        for k,v in ambulances.iteritems():
            self.ambulances[k] = {"pos": copy.deepcopy(v), "path":None, "route": [[v.lat, v.lon]], "incidentId": None}
            self.log(self.t, "init",{"responderId": k, "pos": v, "type":"ambulance"})
        
    def advance(self):
        def advanceResponders(responders):
            removed = []
            for responderId, responder in responders.iteritems():
                if responder["path"] !=  None:
                    i = 0
                    path = responder["path"]
                    while i < len(path) and path[i][0] < self.t:
                        i+=1
                    
                    self.log(self.t, "moved", {"responderId":responderId, "pos": path[i][1]})
                    
                    if i >= len(path)-1:
                        #arrived
                        if DEBUG:
                            print self.uidString+("[t=" + str(self.t) + "]").ljust(8) + " responder "+ responderId + " arrived at incident " + str(responder["incidentId"])
                        self.log(self.t, "resolved", {"responderId": responderId, "responderPos": path[i][1], "incidentId": responder["incidentId"]})
                        i = len(path) -1
                        arrivedAt = path[i][0]
                        removed.append(self.getIncident(responder["incidentId"]))
                        self.resolveIncident(responder["incidentId"], arrivedAt)
                        responder["path"] = None
                        responder["route"] = None
                        responder["incidentId"] = None
                    else:
                        r = Routing(1.0)
                        responder["path"] = path[i:]
                        responder["route"] = r.advanceOnRoute(responder["route"], path[i][0]-path[0][0])
                        
                    responder["pos"] = path[i][1]
                    if responder["route"] == None:
                        responder["route"] = [[responder["pos"].lat, responder["pos"].lon]]
            return removed
                    
        def refreshIncidents():
            added = True
            addedIncidents = []
            while added:
                added = False
                toAdd = []
                for inc in self.activeIncidents:
                    toSpawn = []
                    for child in inc.children:
                        if child.time <= self.t:
                            if DEBUG:
                                print self.uidString+("[t=" + str(self.t) + "]").ljust(8) + " incident " + str(inc.uid).rjust(4) + " ["+(inc.incidentType+"]").ljust(8) + " spreaded [" + str(child.uid) +"]"
                            self.log(self.t, "spreaded", {"parentId": inc.uid, "incidentId": child.uid, "pos": child.pos, "type": child.incidentType})
                            toSpawn.append(child)
                    for child in toSpawn:
                        inc.children.remove(child)
                        toAdd.append(child)
                        
                addedIncidents.extend(toAdd)
                for child in toAdd:
                    self.activeIncidents.append(child)
                    added = True
            return addedIncidents
        
        self.t += 1
        
        added = []
        removed = []
        
        for incident in self.eventTree:
            if incident.time <= self.t and incident not in self.activeIncidents and incident.uid not in self.resolvedIncidentIds:
                if DEBUG:
                    print self.uidString+("[t=" + str(self.t) + "]").ljust(8) + " incident " + str(incident.uid).rjust(4) + " ["+(incident.incidentType+"]").ljust(8) + " spawned"
                self.log(self.t, "spawned", {"incidentId": incident.uid, "pos": incident.pos, "type": incident.incidentType})
                added.append(incident)
                self.activeIncidents.append(incident)
        #remove from eventTree if added
        #[self.eventTree.remove(x) for x in added]
        
        
        removed.extend(advanceResponders(self.fireFighters))
        removed.extend(advanceResponders(self.officers))
        removed.extend(advanceResponders(self.ambulances))
        
        added.extend(refreshIncidents())
        
        #self.accumulatedIncidents += len(self.activeIncidents)
        
        return {"added": added, "removed": removed}
        
    
    def resolveIncident(self, incidentId, arrivalTime):
        incident = None
        for tIncident in self.activeIncidents:
            if tIncident.uid == incidentId or str(tIncident.uid) == incidentId:
                incident = tIncident
        if incident == None:
            if DEBUG:
                print self.uidString+("[t=" + str(self.t) + "]").ljust(8) + " couldn't resolve incident + " +str(incidentId)+ "  - has been solved already?"
        else:
            childCount = self.countChildren(incident)
            self.currentScore += float(self.timespan - self.t + incident.time + self.timespan * childCount)/float(self.timespan * self.maxChildCount)*10000.0
            self.activeIncidents.remove(incident)
            self.resolvedIncidentIds.append(incidentId)
            if DEBUG:
                print self.uidString+("[t=" + str(self.t) + "]").ljust(8) + " incident " + str(incident.uid).rjust(4) + " ["+(incident.incidentType+"]").ljust(8) + " was resolved"
        
    def countChildren(self, incident):
        num = 0
        for child in incident.children:
            num += self.countChildren(child)
        num +=1
        return num
            
    
    def getResponders(self):
        responders = {}
        responders["fireFighters"] = dict([(name, {'route': f['route'], 'speed': Routing.MOVING_SPEED } ) for name, f in self.fireFighters.iteritems()])
        responders["officers"] = dict([(name, {'route': o["route"], 'speed': Routing.MOVING_SPEED}) for name, o in self.officers.iteritems()])
        responders["ambulances"] = dict([(name, {'route': a["route"], 'speed': Routing.MOVING_SPEED}) for name, a in self.ambulances.iteritems()])
        return responders
    
    def getResponderDetails(self, responderId):
        if responderId in self.fireFighters:
            return self.fireFighters[responderId]
        elif responderId in self.officers:
            return self.officers[responderId]
        elif responderId in self.ambulances:
            return self.ambulances[responderId]
    
    def assignToIncident(self, responderId, incidentId):
        if incidentId == 11:
            pass
        incident = self.getIncident(incidentId)
        responder = None
        if responderId in self.fireFighters and incident.incidentType == "fire":
            responder = self.fireFighters[responderId]
        elif responderId in self.officers and incident.incidentType == "looters":
            responder = self.officers[responderId]
        elif responderId in self.ambulances and incident.incidentType == "injury":
            responder = self.ambulances[responderId]
        
        if responder == None:
            raise Exception("responder '" + responderId + "' does not exist or cannot cover incident of type '" + incident.incidentType + "'")
        
        r = routing.Routing()
        p = responder["pos"]
        route = r.route(p.lat, p.lon, incident.pos.lat, incident.pos.lon)
        
        responder["incidentId"] = incident.uid
        responder["path"] = []
        responder["route"] = route["route"]["coordinates"]
        for timecoord in route['timecoords']:
            responder["path"].append([self.t + timecoord[0], Position(timecoord[1], timecoord[2])])
        if DEBUG:
            print self.uidString+("[t=" + str(self.t) + "]").ljust(8) +" assigned responder " + responderId + " to incident " + str(incidentId) + " with planned arrival at t = " + str(responder["path"][len(responder["path"])-1][0])
        self.log(self.t, "assignResponder", {"responder": responderId, "incidentId": incidentId})
        return route
    
    def end(self):
        self.log(self.t, "finished", {"score": self.getCurrentUtility()})
    
    def log(self, time, action, parameters):
        if self.logfolder:
            with open(self.logfolder, 'a') as f:
                f.write(str(time))
                f.write(",")
                f.write(action)
                f.write(",{")
                for k,v in parameters.iteritems():
                    f.write(str(k))
                    f.write(": ")
                    f.write(str(v))
                    f.write(",")
                f.write("}\n")
    
    def getIncident(self, incidentId):
        for incident in self.activeIncidents:
            if incident.uid == incidentId or str(incident.uid) == incidentId:
                return incident
        return None
    
    def getActiveIncidents(self):
        incidents = {}
        incidents['fire'] = {}
        incidents['looters'] = {}
        incidents['injury'] = {}
        
        for incident in self.activeIncidents:
            incidents[incident.incidentType][incident.uid] = incident.pos
            
        return incidents
        
    def getCurrentUtility(self):
        return self.currentScore
        #return self.t * SimulationState.AVG_ACTIVE_INCIDENTS - self.accumulatedIncidents

class Simulation:
    
    def __init__(self, simulationId, timespan, eventTree, fireFighters, officers, ambulances):
        self.lock = threading.RLock()
        
        self.simulationId = simulationId
        self.currentUserId = 0
        self.timespan = timespan
        self.eventTree = eventTree
        self.users = {}
        self.fireFighters = fireFighters
        self.officers = officers
        self.ambulances = ambulances
        self.t = 0
        self.started = False
        self.agents = {}
        self.isReady = True;
        self.simulationHash = None
        
    def clone(self):
        return Simulation(self.simulationId, self.timespan, copy.deepcopy(self.eventTree) , copy.deepcopy(self.fireFighters), copy.deepcopy(self.officers), copy.deepcopy(self.ambulances))
        
    def addUser(self, actionMap = None, logging = False):
        if not self.started:
            self.currentUserId += 1
            logFolder= False
            if logging:
                logFolder = LOG_FOLDER+"/"+self.simulationHash
            self.users[self.currentUserId] = SimulationState(self.currentUserId, self.timespan, self.eventTree, copy.deepcopy(self.fireFighters), copy.deepcopy(self.officers), copy.deepcopy(self.ambulances), logFolder)
            if actionMap != None:
                self.agents[self.currentUserId] = actionMap
                self.users[self.currentUserId].uidString = ("[agentId=" + str(self.currentUserId)+"]").ljust(13)
            return self.currentUserId
        else:
            return -1
        
    def setAgentActions(self,agentId, actionMap):
        self.agents[agentId] = actionMap
        
    def advance(self):
        with self.lock:
            if self.started:
                self.t += 1
                updates = {}
                for userId, user in self.users.iteritems():
                    updates[userId] = user.advance()
                    if userId in self.agents:
                        if self.t in self.agents[userId]:
                            for action in self.agents[userId][self.t]:
                                self.assignToIncident(action['responderId'], action['incidentId'], userId)
                return updates
            else:
                return None
    
    def assignToIncident(self, responderId, incidentId, userId):
        with self.lock:
            if self.started:
                return self.users[userId].assignToIncident(responderId, incidentId)
            return -1
        
    def getActiveIncidents(self, userId):
        if not self.hasFinished():
            return self.users[userId].getActiveIncidents()
        else:
            return []
    
    def getResponders(self, userId):
        if not self.hasFinished():
            return self.users[userId].getResponders()
        else:
            return []
    
    def getResponderDetails(self, userId, responderId):
        return self.users[userId].getResponderDetails(responderId)
    
    def hasFinished(self):
        return self.t >= self.timespan
    
    def start(self):
        self.started = True
        
    def end(self):
        self.resultMap = {}
        for userId, user in self.users.iteritems():
            self.resultMap[userId] = user.getCurrentUtility()
            user.end()
            print self.users[userId].uidString+ "finished with a score of " + str(int(self.resultMap[userId]))
        self.users = []
        
    def getCurrentUtility(self, userId):
        if self.hasFinished():
            return self.resultMap[userId]
        return self.users[userId].getCurrentUtility()
            
class Manager:
    
    currentId = 0
    
    def __init__(self):
        self.lock = threading.RLock()
        self.simulations = {}
        if not os.path.exists(STORED_TREES_FOLDER):
            os.mkdir(STORED_TREES_FOLDER)
        if not os.path.exists(AGENT_ACTIONS_FOLDER):
            os.mkdir(AGENT_ACTIONS_FOLDER)
        if not os.path.exists(LOG_FOLDER):
            os.mkdir(LOG_FOLDER)
    
    def createSimulation(self, simulationTreeGenerator, nFireFighters, nOfficers, nAmbulances):
        def parseReadInTree(tree, node):
            position = Position(float(node["pos"]["lat"]), float(node["pos"]["lon"]))
            incident = Incident(int(node["uid"]), node["incidentType"], int(node["time"]), position)
            tree.append(incident)
            for child in node["children"]:
                parseReadInTree(incident.children, child)
                
        def parseResponders(responders):
            parsedResponders = {}
            for r, pos in responders.iteritems():
                parsedResponders[r]  = Position(float(pos["lat"]), float(pos["lon"]))
            return parsedResponders
        
        Manager.currentId += 1
        simId = Manager.currentId
        
        
        eventTree = []
        # check if tree has already been generated
        simuHash = simulationTreeGenerator.hash()
        treepath = STORED_TREES_FOLDER + "/" + simuHash
        if os.path.isfile(treepath):
            try:
                f = open(treepath)
                info = json.loads(f.read())
                tempTree = info["eventTree"]
                fireFighters = parseResponders(info["fireFighters"])
                ambulances = parseResponders(info["ambulances"])
                officers = parseResponders(info["officers"])
                eventTree = []
            finally:
                f.close()
            for node in tempTree:
                parseReadInTree(eventTree, node)
        else:
            fireFighters = {}
            for i in range(nFireFighters):
                name = "fireFighter"+str(i).zfill(int(math.floor(math.log10(nFireFighters))+1))
                pos = simulationTreeGenerator.getRandomPosition()
                fireFighters[name] = pos
            
            officers = {}
            for i in range(nOfficers):
                name = "officer"+str(i).zfill(int(math.floor(math.log10(nOfficers))+1))
                pos = simulationTreeGenerator.getRandomPosition()
                officers[name] = pos
            
            ambulances = {}
            for i in range(nAmbulances):
                name = "ambulance"+str(i).zfill(int(math.floor(math.log10(nAmbulances))+1))
                pos = simulationTreeGenerator.getRandomPosition()
                ambulances[name] = pos
                
            eventTree = simulationTreeGenerator.simulate()
            with open(treepath, 'w') as f:
                dump = {"eventTree": eventTree, "fireFighters": fireFighters, "officers": officers, "ambulances": ambulances}
                f.write(json.dumps(dump, default=lambda o: o.__dict__, sort_keys=True, indent=1))
                
        self.simulations[simId] = Simulation(simId, simulationTreeGenerator.timespan, eventTree, fireFighters, officers, ambulances)
        self.simulations[simId].simulationHash = simuHash
        return simId
    
    def isReady(self, simulationId):
        return self.simulations[simulationId].isReady
    
    def registerUser(self, simulationId):
        return self.simulations[simulationId].addUser(None, True)
    
    def advanceSimulation(self, simulationId = None):
        if simulationId == None:
            simulationId = Manager.currentId
        return self.simulations[simulationId].advance()
        
    def assignToIncident(self, responderId, incidentId, userId, simulationId = None):
        if simulationId == None:
            simulationId = Manager.currentId
        simu = self.simulations[simulationId]
        return simu.assignToIncident(responderId, incidentId, userId)
    
    def activeSimulations(self):
        activeSimulations = []
        for simuId, simulation in self.simulations.iteritems():
            if not simulation.started:
                activeSimulations.append(simuId)
        return activeSimulations
    
    def startSimulation(self, simulationId):
        runner = SimulationRunner(self.simulations[simulationId], 1.0)
        runner.start() 
    
    def executeAgentForSimulation(self, simulationId):
        fn = AGENT_ACTIONS_FOLDER + "/" + self.simulations[simulationId].simulationHash
        if os.path.isfile(fn):
            with open(fn, 'r') as f:
                t = f.read();
                unpolishedActions = json.loads(t)
                actions = {}
                for k, v in unpolishedActions.iteritems():
                    actions[int(k)] = v
                print "agent was read in" 
                print "read in actions\n" + str(actions)
                return self.simulations[simulationId].addUser(actions)
        else:
            self.simulations[simulationId].isReady = False
            s = self.simulations[simulationId].clone();
            agentId = self.simulations[simulationId].addUser({});
            runner = SimulationRunner(s, 0, s.addUser(), agentId, self)
            actions = runner.start()
            return agentId

    def setAgentActions(self, simId, agentId, actionMap):
        fn = AGENT_ACTIONS_FOLDER + "/" + self.simulations[simId].simulationHash
        with open(fn, 'w') as f:
            f.write(json.dumps(actionMap))
        self.simulations[simId].setAgentActions(agentId,actionMap)   
        self.simulations[simId].isReady = True
            
    def hasFinished(self, simulationId):
        return self.simulations[simulationId].hasFinished()
        
    def getActiveIncidents(self, simulationId, userId):
        return self.simulations[simulationId].getActiveIncidents(userId)    
    
    def getResponders(self, simulationId, userId):
        return self.simulations[simulationId].getResponders(userId)
    
    def getResponderDetails(self, simulationId, userId, responderId):
        return self.simulations[simulationId].getResponderDetails(userId, responderId)
    
    def getCurrentUtility(self, simulationId, userId):
        return self.simulations[simulationId].getCurrentUtility(userId)
    
    def getScoreBoard(self):
        fn= getScoreboardFileForToday()
        scores = []
        if os.path.exists(fn):
            with open(fn,'r') as f:
                for line in f:
                        score = int(line)
                        scores.append(score)
            scores.sort(reverse=True)
        return scores
    
    def writeScore(self, score):
        filename = getScoreboardFileForToday()
        with self.lock:
            with open(filename,'a') as f:
                f.write(str(score) +"\n")
    
if False:
    gen = SimulationTreeGenerator(4, 50, 1, 52.455158, -1.949639, 52.444748, -1.921165,3,2,2)
    m = Manager()
    simId = m.createSimulation(gen, 2, 2, 2)
    m.executeAgentForSimulation(simId)
    #userId = m.registerUser(simId)
    #m.assignToIncident("fireFighter0", 10,  userId, simId)
    
    #for i in range(100):
    #    m.advanceSimulation(simId)
    #    if i == 21:
    #        m.assignToIncident("fireFighter0", 10,  userId, simId)
    #    if i == 34:
    #        m.assignToIncident("fireFighter3", 16, userId, simId)
    

            