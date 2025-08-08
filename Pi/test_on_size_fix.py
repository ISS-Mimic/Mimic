#!/usr/bin/python

# Test the on_size method fix
from Screens.orbit_screen import Orbit_Screen

def test_on_size_method():
    """Test that the on_size method works without errors."""
    print("Testing on_size method fix:")
    
    try:
        # Create orbit screen instance
        orbit_screen = Orbit_Screen()
        
        # Test the on_size method
        orbit_screen.on_size(800, 600)  # Simulate size change
        print("✓ on_size method works without errors")
        
        # Test with different sizes
        orbit_screen.on_size(1920, 1080)
        orbit_screen.on_size(1024, 768)
        print("✓ on_size method handles different screen sizes")
        
    except Exception as e:
        print(f"✗ on_size method failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("on_size method test completed successfully!")
    return True

if __name__ == '__main__':
    test_on_size_method() 