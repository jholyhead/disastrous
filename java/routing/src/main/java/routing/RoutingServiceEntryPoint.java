package routing;

import py4j.GatewayServer;

public class RoutingServiceEntryPoint {
	
	private RoutingService rs;
	
	public RoutingServiceEntryPoint(String ghLoc, String mapsLoc){
		rs = new RoutingService(ghLoc, mapsLoc);
	}
	
	public RoutingService getRoutingService(){
		return rs;
	}

	public static void main(String[] args) {
		String loc, maps;
		if(args.length <2){
			loc = "D:/tmp/loc";
			maps="D:/tmp/birmingham.osm.pbf";
		} else{
			loc = args[0];
			maps = args[1];
		}
		GatewayServer gatewayServer = new GatewayServer(new RoutingServiceEntryPoint(loc, maps));
		gatewayServer.start();
	}

}
