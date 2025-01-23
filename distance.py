import openrouteservice

def get_road_distance(api_key, origin, destination):
    # Initialize OpenRouteService client
    client = openrouteservice.Client(key=api_key)
    
    # Geocode the origin
    origin_response = client.pelias_search(origin)
    if not origin_response['features']:
        raise ValueError(f"Origin address '{origin}' not found.")
    origin_coords = origin_response['features'][0]['geometry']['coordinates']
    
    # Geocode the destination
    destination_response = client.pelias_search(destination)
    if not destination_response['features']:
        raise ValueError(f"Destination address '{destination}' not found.")
    destination_coords = destination_response['features'][0]['geometry']['coordinates']
    
    # Get the route between the two coordinates
    route = client.directions(coordinates=[origin_coords, destination_coords], 
                              profile='driving-car',
                              format='json')
    
    # Extract road distance (in meters)
    distance_meters = route['routes'][0]['summary']['distance']
    distance_km = distance_meters / 1000  # Convert to kilometers
    
    return distance_km

# Replace with your OpenRouteService API key
api_key = "5b3ce3597851110001cf62480ffddd3bb04f46f395f4acfa79b69588"

origin = "Ex servicemen colony, VG rao nagar"
destination = "Ottakkalmandapam, Tamilnadu"

try:
    distance = get_road_distance(api_key, origin, destination)
    print(f"The road distance between '{origin}' and '{destination}' is {distance:.2f} km.")
except Exception as e:
    print(f"Error: {e}")
