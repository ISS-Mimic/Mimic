#!/usr/bin/python

# Minimal test for user location coordinates
import math

def test_coordinates():
    # Test coordinates (Houston, New York, Los Angeles)
    test_locations = [
        (29.585736, -95.1327829, "Houston"),
        (40.7128, -74.0060, "New York"),
        (34.0522, -118.2437, "Los Angeles"),
        (51.5074, -0.1278, "London"),
        (35.6762, 139.6503, "Tokyo")
    ]
    
    print("Testing coordinate conversions:")
    for lat, lon, name in test_locations:
        # Simple coordinate validation
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            print(f"✓ {name}: {lat}, {lon} - Valid coordinates")
        else:
            print(f"✗ {name}: {lat}, {lon} - Invalid coordinates")
    
    print("Coordinate validation test completed!")

if __name__ == '__main__':
    test_coordinates() 