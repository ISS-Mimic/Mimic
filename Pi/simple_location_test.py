#!/usr/bin/python

# Test user location functionality without loading the full orbit screen
from Screens.orbit_screen import Orbit_Screen

def test_user_location():
    # Create orbit screen instance
    orbit_screen = Orbit_Screen()
    
    print("Testing user location functionality:")
    print(f"Default location: {orbit_screen.user_lat}, {orbit_screen.user_lon}")
    
    # Test setting a new location
    orbit_screen.set_user_location(40.7128, -74.0060)  # New York
    print(f"New location: {orbit_screen.user_lat}, {orbit_screen.user_lon}")
    
    # Test another location
    orbit_screen.set_user_location(34.0522, -118.2437)  # Los Angeles
    print(f"Another location: {orbit_screen.user_lat}, {orbit_screen.user_lon}")
    
    # Test map coordinate conversion
    x, y = orbit_screen.map_px(orbit_screen.user_lat, orbit_screen.user_lon)
    print(f"Map coordinates: {x}, {y}")
    
    print("User location functionality test completed successfully!")

if __name__ == '__main__':
    test_user_location() 