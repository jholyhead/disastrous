package routing;

import com.graphhopper.GHRequest;
import com.graphhopper.GHResponse;
import com.graphhopper.GraphHopper;
import com.graphhopper.routing.util.DefaultEdgeFilter;
import com.graphhopper.routing.util.EncodingManager;
import com.graphhopper.storage.index.QueryResult;
import com.graphhopper.util.PointList;

public class RoutingService {

	GraphHopper hopper;
	
	public RoutingService(String ghLoc, String filepath){
		hopper = new GraphHopper().setInMemory(true).
				setEncodingManager(new EncodingManager(EncodingManager.FOOT)).
				setElevation(false).
				setEnableInstructions(false).
				setGraphHopperLocation(ghLoc).
				setOSMFile(filepath);
		hopper.importOrLoad();
	}
	
	public String getRoute(double startLat, double startLong, double endLat, double endLong){
		GHResponse route = hopper.route(new GHRequest(startLat, startLong, endLat, endLong));
		if(!route.isFound() || route.getPoints().size() == 0){
			PointList list = new PointList(1, false);
			list.add(startLat, startLong);
			route.setPoints(list);
		}
		StringBuilder sb = new StringBuilder("{\n \"geoJson\": \n");
		sb.append(this.toGetJSON(route));
		sb.append(",\n \"distance\": ");
		sb.append(route.getDistance());
		sb.append("\n}");
		return sb.toString();
	}
	
	public String getNearestPosition(double lat, double lon){
		QueryResult result = hopper.getLocationIndex().findClosest(lat, lon, new DefaultEdgeFilter(hopper.getEncodingManager().getSingle()));
		lat = result.getSnappedPoint().getLat();
		lon = result.getSnappedPoint().getLon();
		StringBuilder sb = new StringBuilder();
		sb.append(lat);
		sb.append(",");
		sb.append(lon);
		return sb.toString();
	}
	
	private String toGetJSON(GHResponse response){
		StringBuilder sb = new StringBuilder("\t\t{\n"
				+ "\t\t\t\"type\": \"LineString\",\n"
				+ "\t\t\t\"coordinates\": [" );
		PointList points = response.getPoints();
		for(Double[] arr : points.toGeoJson()){
			sb.append("[");
			sb.append(arr[1]);
			sb.append(", ");
			sb.append(arr[0]);
			sb.append("],");
		}
		sb.delete(sb.length()-1, sb.length());
		sb.append("]\n\t\t}");
		return sb.toString();
	}
}
