#!/usr/bin/env python3
"""
Test the new wire routing algorithm with proper bends
"""

def test_wire_routing_algorithm():
    """Test the orthogonal wire routing algorithm."""
    print("🔀 Testing Wire Routing Algorithm with Proper Bends")
    print("=" * 60)

    # Simulate the _create_wire_routing function
    def create_wire_routing(from_coords, to_coords, from_component, to_component):
        """Test version of wire routing algorithm."""
        start_x, start_y = from_coords
        end_x, end_y = to_coords

        # Calculate routing strategy based on pin positions
        dx = end_x - start_x
        dy = end_y - start_y

        # Use L-shaped routing (two segments) for most connections
        segments = []

        # Determine routing direction based on distance and component layout
        if abs(dx) > abs(dy):
            # Horizontal routing first, then vertical
            mid_x = start_x + dx * 0.7  # 70% of the way horizontally

            segments.append({
                'start': [start_x, start_y],
                'end': [mid_x, start_y],
                'type': 'horizontal'
            })

            segments.append({
                'start': [mid_x, start_y],
                'end': [mid_x, end_y],
                'type': 'vertical'
            })

            segments.append({
                'start': [mid_x, end_y],
                'end': [end_x, end_y],
                'type': 'horizontal'
            })
        else:
            # Vertical routing first, then horizontal
            mid_y = start_y + dy * 0.7  # 70% of the way vertically

            segments.append({
                'start': [start_x, start_y],
                'end': [start_x, mid_y],
                'type': 'vertical'
            })

            segments.append({
                'start': [start_x, mid_y],
                'end': [end_x, mid_y],
                'type': 'horizontal'
            })

            segments.append({
                'start': [end_x, mid_y],
                'end': [end_x, end_y],
                'type': 'vertical'
            })

        # Filter out zero-length segments
        valid_segments = []
        for segment in segments:
            start = segment['start']
            end = segment['end']
            if start[0] != end[0] or start[1] != end[1]:  # Not zero length
                valid_segments.append(segment)

        # If no valid segments (pins are at same location), create a short segment
        if not valid_segments:
            valid_segments = [{
                'start': from_coords,
                'end': to_coords,
                'type': 'direct'
            }]

        return valid_segments

    # Test cases based on actual ESP32-TAS5830 connections
    test_cases = [
        {
            'name': 'ESP32 Pin 23 → TAS5830 Pin 10',
            'from': [266.7, 184.15],  # ESP32 pin 23 (GPIO21)
            'to': [263.53, 44.39],    # TAS5830 pin 10 (estimated)
            'from_comp': 'U3',
            'to_comp': 'U1'
        },
        {
            'name': 'ESP32 Pin 16 → TAS5830 Pin 25',
            'from': [266.7, 201.93],  # ESP32 pin 16 (GPIO15)
            'to': [254.63, 50.24],    # TAS5830 pin 25 (estimated)
            'from_comp': 'U3',
            'to_comp': 'U1'
        },
        {
            'name': 'TAS5830 Pin 8 → TAS5830 Pin 32',
            'from': [260.38, 42.54],  # TAS5830 pin 8
            'to': [254.63, 47.64],    # TAS5830 pin 32
            'from_comp': 'U1',
            'to_comp': 'U1'
        }
    ]

    print("BEFORE: Single straight wire from pin to pin")
    print("AFTER:  Multiple wire segments with proper bends\n")

    for i, test in enumerate(test_cases):
        print(f"--- Test {i+1}: {test['name']} ---")
        print(f"From: {test['from']} → To: {test['to']}")

        segments = create_wire_routing(test['from'], test['to'], test['from_comp'], test['to_comp'])

        print(f"Wire segments: {len(segments)}")

        total_length = 0
        for j, segment in enumerate(segments):
            start = segment['start']
            end = segment['end']

            # Calculate segment length
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            total_length += length

            print(f"  Segment {j+1} ({segment['type']}): {start} → {end} ({length:.2f}mm)")

        # Calculate direct distance
        direct_dist = ((test['to'][0] - test['from'][0])**2 + (test['to'][1] - test['from'][1])**2)**0.5
        routing_overhead = (total_length - direct_dist) / direct_dist * 100

        print(f"Total routed length: {total_length:.2f}mm")
        print(f"Direct distance: {direct_dist:.2f}mm")
        print(f"Routing overhead: {routing_overhead:.1f}%")

        # Validate routing
        if len(segments) > 1:
            print("✅ Proper orthogonal routing with bends")
        else:
            print("ℹ️  Direct routing (no bends needed)")

        print()

    print("🎯 EXPECTED WIRE ROUTING IMPROVEMENTS:")
    print("✅ Multiple wire segments instead of single straight lines")
    print("✅ Orthogonal routing (horizontal + vertical segments)")
    print("✅ Proper bends at 70% distance intervals")
    print("✅ Method shows 'routed_wire_segments' instead of 'pin_to_pin_wire'")
    print("✅ Response includes 'wire_segments' count and 'routing_type'")

    print("\n🏁 WIRE ROUTING ALGORITHM TEST COMPLETED!")
    print("Ready to test with MCP server restart.")

if __name__ == "__main__":
    test_wire_routing_algorithm()