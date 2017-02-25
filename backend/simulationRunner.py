'''
Created on 30 Aug 2014

@author: fa1c12
'''

import threading
import time
import subprocess
import os.path
import shutil
import json
from routing import Routing

DEBUG = False
PATH_TO_AGENT = './backend/workdir'
PATH_FROM_AGENT_TO_HERE = '.'

class SimulationRunner(threading.Thread):
    
    def __init__(self, simulation, interval, agent = None, agentId = None, parent = None):
        threading.Thread.__init__(self)
        self.simulation = simulation
        self.interval = interval
        self.agent = agent
        self.parent = parent
        self.agentId = agentId
        
        if self.agent != None:
            self.workingDir = 'agent_temp/tmp' + str(self.simulation.simulationId)
            if os.path.exists(self.workingDir):
                shutil.rmtree(self.workingDir)
            os.makedirs(self.workingDir)
            
            self.actionList = {}
            self.currentIncidentForResponder = {}
            self.pairings = ( ('fire', 'fireFighters'), ('injury', 'ambulances'), ('looters', 'officers'))
    
    def run(self):
        self.simulation.start()
        
        while not self.simulation.isReady:
            time.sleep(1)
        
        updates = self.simulation.advance()
        while not self.simulation.hasFinished():
            if self.agent == None:
                if DEBUG:
                    "advanced simulation " + str(self.simulation.simulationId) + " to " + str(self.simulation.t)
                time.sleep(self.interval)
            elif updates != None:
                for userId, changes in updates.iteritems():
                    if userId == self.agent and (len(changes['added']) > 0 or len(changes['removed']) > 0):
                        # create matrices
                        responderToIncident = self.createResponderToIncidentMatrices()
                        incidentToIncident = self.createIncidentToIncidentMatrices()
                        
                        for incidentType, responderType in self.pairings:
                            results = self.writeAgentFile(self.workingDir+"/" + incidentType, responderToIncident[responderType], incidentToIncident[incidentType])
                            filename = results['name']
                            responderOrder = results['responderOrder']
                            incidentOrder = results['incidentOrder']
                            
                            output = subprocess.check_output([PATH_TO_AGENT + "/SFAgent.exe", PATH_FROM_AGENT_TO_HERE + "/" + filename])
                            with open(filename+"result",'w') as f:
                                f.write(str(output))
                            
                            for line in output.split('\n'):
                                if line.startswith('['):
                                    line = line.replace(";","")
                                    parsed = json.loads(line)
                                    for i in range(len(parsed)):
                                        responderId = responderOrder[i]
                                        if len(parsed[i]) > 0:
                                            incidentId = incidentOrder[parsed[i][0]]
                                            if responderId not in self.currentIncidentForResponder or self.currentIncidentForResponder[responderId] != incidentId:
                                                self.addAction(self.simulation.t, responderId, incidentId )
            updates = self.simulation.advance()
                        
        self.simulation.end()
        if DEBUG:
            agent = ' (agent)' if self.agent != None else ''
            print "simulation " + str(self.simulation.simulationId) + agent + " ended"
            
        if self.agent != None:
            self.parent.setAgentActions(self.simulation.simulationId, self.agentId, self.actionList)
            
    def addAction(self, t, responderId, incidentId):
        if t not in self.actionList:
            self.actionList[t] = []
        self.actionList[t].append({'responderId': responderId, 'incidentId': incidentId})
        self.currentIncidentForResponder[responderId] = incidentId
        self.simulation.assignToIncident(responderId, incidentId, self.agent )
        
            
    def writeAgentFile(self, filename, responderToIncident, incidentToIncident):
        counter = 0
        name = filename
        while os.path.isfile(name):
            counter+=1
            name = filename+str(counter)
        with open(name, 'w') as f:
            f.write("timeLimit = 10;\n")
            
            responderOrder= sorted(responderToIncident.keys())
            incidentOrder = sorted(responderToIncident[responderToIncident.keys()[0]].keys())
            
            f.write("nofAgents = " + str(len(responderOrder))+";\n")
            f.write("nofTasks = " + str(len(incidentOrder))+";\n")
            
            responderToIncidentMatrix = []
            for responder in responderOrder:
                incidentDistances = []
                for incident in incidentOrder:
                    incidentDistances.append(responderToIncident[responder][incident])
                # append trailing 0
                incidentDistances.append(0)
                
                responderToIncidentMatrix.append(incidentDistances)
    
            f.write("travelAT = " + str(responderToIncidentMatrix) + ";\n")
            
            incidentToIncidentMatrix = []
            for i1 in incidentOrder:
                distances = []
                for i2 in incidentOrder:
                    if i1 == i2:
                        distances.append(0)
                    else:
                        distances.append(incidentToIncident[i1][i2])
                #append trailing 0
                distances.append(0)
                
                incidentToIncidentMatrix.append(distances)
            incidentToIncidentMatrix.append([0 for _ in incidentOrder])
            
            f.write("travelTT = " + str(incidentToIncidentMatrix) + ";\n")
            
        return {'name': name, 'responderOrder': responderOrder, 'incidentOrder': incidentOrder}
            
    def createResponderToIncidentMatrices(self):
        responders = self.simulation.getResponders(self.agent)
        incidents = self.simulation.getActiveIncidents(self.agent)
        
        distances = {}
        router = Routing()
        
        for t, respondersByType in responders.iteritems():
            distances[t] = {}
            for responderId, data in respondersByType.iteritems():
                lat, lon = data["route"][0]
                distances[t][responderId]= {}
                incidentType = "fire" if t == "fireFighters" else "injury" if t == "ambulances" else "looters"
                for incident, incidentPos in incidents[incidentType].iteritems():
                    distance = len(router.route(lat, lon, incidentPos.lat, incidentPos.lon)['timecoords'])
                    distances[t][responderId][incident] = distance
        return distances
    
    def createIncidentToIncidentMatrices(self):
        distances = {}
        incidentMap = self.simulation.getActiveIncidents(self.agent)
        router = Routing()
        
        for incidentType, incidents  in incidentMap.iteritems():
            distances[incidentType] = {}
            for incidentId, pos in incidents.iteritems():
                for incident2Id, pos2 in incidents.iteritems():
                    if incidentId != incident2Id:
                        if incidentId not in distances[incidentType]:
                            distances[incidentType][incidentId] = {}
                        if incident2Id in distances[incidentType] and incidentId in distances[incidentType][incident2Id]:
                            distances[incidentType][incidentId][incident2Id] = distances[incidentType][incident2Id][incidentId]
                        else:
                            distance = len(router.route(pos.lat, pos.lon, pos2.lat, pos2.lon)['timecoords'])
                            distances[incidentType][incidentId][incident2Id] = distance
                            distances[incidentType][incidentId][incident2Id] = distance
                        
        return distances
                