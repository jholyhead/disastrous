'''
Created on 7 Aug 2014

@author: fa1c12
'''
import os
import web
import json
import traceback
import random
from simulationTreeGenerator import SimulationTreeGenerator
from routing import Routing
from simulationManager import Manager

urls = ('/disaster', 'disaster',
	  '/agentDisaster', 'agentDisaster',
	  '/createSimulation', 'createSimulation',
	  '/(.+)/connectUser', 'connectUser',
	  '/(.+)/addAgent', 'addAgent',
	  '/(.+)/start', 'startSimulation',
	  '/(.+)/(.+)/assignToIncident', 'assignToIncident',
	  '/(.+)/(.+)/incidents', 'incidents',
	  '/(.+)/(.+)/score', 'score',
	  '/postScore', 'postScore',
	  '/scoreboard', 'scoreboard',
	  '/(.+)/(.+)/responders', 'responders',
	  '/availableSimulations', 'activeSimulations',
	  '/route', 'route',
	  '/images/(.+)', 'images',
	  '/(.+)', 'fileLoader')

routing = Routing()
manager = Manager()

class Application(web.application):
	def run(self, url="0.0.0.0", port=8080, *middleware):
		func = self.wsgifunc(*middleware)
		return web.httpserver.runsimple(func, (url, port))
		
class disaster:
	# exampleURL:
	# http://localhost:1234/disaster
	def GET(self):
		page = web.template.frender('html/index.html')
		return page()
class agentDisaster:
	# exampleURL:
	# http://localhost:1234/agentDisaster
	def GET(self):
		page = web.template.frender('html/agentIndex.html')
		return page()
class fileLoader:
	# exampleURL:
	# http://localhost:1234/*****
	def GET(self, name):
		with open('html/%s' % name, "r") as f:
			return f.read()
		raise web.notfound()

class images:
	def GET(self, name):
		ext = name.split(".")[-1]  # Gather extension

		cType = {
			"png":"images/png",
			"jpg":"images/jpeg",
			"gif":"images/gif",
			"ico":"images/x-icon"			}

		if name in os.listdir('html/images'):  # Security
			web.header("Content-Type", cType[ext])  # Set the Header
			return open('html/images/%s' % name, "rb").read()  # Notice 'rb' for reading images
		else:
			raise web.notfound()
	
	
class connectUser:
	
	def GET(self, simulationId):
		# exampleURL:
		# http://localhost:1234/1/connectUser
		
		simulationId = int(simulationId)
		
		try:
			userId = manager.registerUser(simulationId)
		except Exception as e:
			traceback.print_exc()
			userId = 'ERROR - ' + str(e)
					
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(userId))
	
class addAgent:
	
	def GET(self, simulationId):
		
		simulationId = int(simulationId)
		try:
			userId = manager.executeAgentForSimulation(simulationId)
		except Exception as e:
			traceback.print_exc()
			userId = 'ERROR - ' + str(e)
			
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(userId))

class assignToIncident:
	
	def GET(self, simulationId, userId):
		# exampleURL:
		# http://localhost:1234/1/1/assignToIncident?responderId=fireFighter0&incidentId=7
		data = web.input()
		simulationId = int(simulationId)
		userId = int(userId)
		responderId = data.responderId
		incidentId = data.incidentId
		
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		response = {}
		try:
			if not manager.hasFinished(simulationId):
				route = manager.assignToIncident(responderId, incidentId, userId, simulationId)
				# speed = route['distance']/ float(len(route['timecoords'])-1)
				speed = routing.MOVING_SPEED
				response['route'] = route['route']
				response['status'] = 'OK'
				response['speed'] = speed
			else:
				response['status'] = "Simulation finished"
		except Exception as e:
			traceback.print_exc()
			response['status'] = 'ERROR - ' + str(e)
		return '%s(%s)' % (callback_name, json.dumps(response))

class startSimulation:
	
	def GET(self, simulationId):
		# exampleURL:
		# http://localhost:1234/1/start
		simulationId = int(simulationId)
		
		response = 'success'
		try:
			manager.startSimulation(simulationId)
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' + str(e)
			
		
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response))

class createSimulation:
	'''
	
	'''
	def GET(self):
		# exampleURL:
		# http://localhost:1234/createSimulation?seed=1&timespan=100&maxChildren=1&minLat=52.455158&minLong=-1.949639&maxLat=52.444748&maxLong=-1.921165&fireFighters=5&officers=5&ambulances=5&initialFires=3&initialInjuries=3&initialLooters=3
		data = web.input()
		if 'seed' in data:
			seed = int(data.seed)
		else:
			seed = int(random.uniform(0, 500))  
		timespan = int(data.timespan)
		maxChildren = int(data.maxChildren)
		minLat = float(data.minLat)
		minLong = float(data.minLong)
		maxLat = float(data.maxLat)
		maxLong = float(data.maxLong)
		if minLat > maxLat:
			minLat, maxLat = maxLat, minLat
		if minLong > maxLong:
			minLong, maxLong = maxLong, minLong
		fireFighters = int(data.fireFighters)	
		officers = int(data.officers)	
		ambulances = int(data.ambulances)  
		initialFires = int(data.initialFires)
		initialInjuries = int(data.initialInjuries)
		initialLooters = int(data.initialLooters)
		
		try:
			handler = SimulationTreeGenerator(seed, timespan, maxChildren, minLat, minLong, maxLat, maxLong, initialFires, initialInjuries, initialLooters)
			simulation = manager.createSimulation(handler, fireFighters, officers, ambulances)
		except Exception as e:
			traceback.print_exc()
			simulation = 'ERROR - ' + str(e)
			
		
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json') 
		return '%s(%s)' % (callback_name, json.dumps(simulation, default=lambda o: o.__dict__, sort_keys=True, indent=2))
		# return json.dumps(handler.simulate(), default=lambda o: o.__dict__,sort_keys=True, indent=2)

class responders:

	def GET(self, simulationId, userId):
		# exampleURL:
		# http://localhost:1234/1/1/responders
		simulationId = int(simulationId)
		userId = int(userId)

		try:
			response = manager.getResponders(simulationId, userId)
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' + str(e)

		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response, default=lambda o: o.__dict__, sort_keys=True, indent=2))
	
class activeSimulations:
	
	def GET(self):
		# exampleURL:
		# http://localhost:1234/availableSimulations
		try:
			response = manager.activeSimulations()
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' + str(e)
	

		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response))
		
class incidents:
	
	def GET(self, simulationId, userId):
		# exampleURL:
		# http://localhost:1234/1/1/incidents
		simulationId = int(simulationId)
		userId = int(userId)
		
		try:
			response = manager.getActiveIncidents(simulationId, userId)
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' + str(e)
		
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response, default=lambda o: o.__dict__, sort_keys=True, indent=2))
	
class score:
	
	def GET(self, simulationId, userId):
		# exampleURL:
		# http://localhost:1234/1/1/score
		simulationId = int(simulationId)
		userId = int(userId)
		
		try:
			response = manager.getCurrentUtility(simulationId, userId)
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' + str(e)
			
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response, default=lambda o: o.__dict__, sort_keys=True, indent=2))
	
class scoreboard:
	
	def GET(self):
		# exampleURL:
		# http://localhost:1234/scoreboard
		
		try:
			response = manager.getScoreBoard()
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' +  str(e)
			
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response))
			
class postScore:
	
	def GET(self):
		# exampleURL:
		# http://localhost:1234/postScore?score=666
		
		score = int(float(web.input().score))
		
		try:
			manager.writeScore(score)
			response = "success"
		except Exception as e:
			traceback.print_exc()
			response = 'ERROR - ' + str(e)
			
		callback_name = web.input(callback='callback').callback
		web.header('Content-Type', 'application/json')
		return '%s(%s)' % (callback_name, json.dumps(response))

class route:
	def GET(self):
		# exampleURL
		# http://localhost:1234/route?startLat=52.455158&startLong=-1.949639&endLat=52.444748&endLong=-1.921165
		data = web.input()
		startLat = float(data.startLat)
		startLon = float(data.startLong)
		endLat = float(data.endLat)
		endLon = float(data.endLong)
		return routing.route(startLat, startLon, endLat, endLon)
		

if __name__ == "__main__":
	app = Application(urls, globals())
	app.run("0.0.0.0", 1234)
