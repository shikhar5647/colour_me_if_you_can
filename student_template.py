import random

class CSP_AGENT:
    """
    A very simple, "stateless" agent for the Graph Coloring assignment.
    - It has no memory.
    - It always moves to a random visible neighbor.
    - It always picks the first legally available color.
    """
    def __init__(self, initial_state):
        """
        This simple agent does not need to initialize any memory.
        """
        print("Simple Stateless Agent initialized.")
        pass

    def get_next_move(self, visible_state):
        """
        This agent's move logic is very simple: it moves to a random adjacent
        node from its current location.
        """
        current_node = visible_state['current_node']
        visible_nodes = visible_state['visible_graph']['nodes']
        
        # Find all nodes we can move to (any visible node other than the current one)
        adjacent_nodes = [n for n in visible_nodes if n != current_node]
        
        if adjacent_nodes:
            move_to = random.choice(adjacent_nodes)
            print(f"Agent says: Moving randomly to '{move_to}'.")
            return {'action': 'move', 'node': move_to}
        else:
            # If there are no other visible nodes, stay put.
            print(f"Agent says: Nowhere to move. Staying at '{current_node}'.")
            return {'action': 'move', 'node': current_node}

    def get_color_for_node(self, node_to_color, visible_state):
        """
        This agent's coloring logic is very simple: it picks the first
        available color that does not conflict with its already-colored
        visible neighbors.
        """
        neighbor_colors = set()
        
        # Find colors used by visible neighbors
        for u, v in visible_state['visible_graph']['edges']:
            neighbor = None
            if u == node_to_color:
                neighbor = v
            elif v == node_to_color:
                neighbor = u
            
            # Check the color of the neighbor in the current observation
            if neighbor and visible_state['node_colors'].get(neighbor) is not None:
                neighbor_colors.add(visible_state['node_colors'][neighbor])

        # Choose the first available color that is not in use by a neighbor.
        for color in visible_state['available_colors']:
            if color not in neighbor_colors:
                print(f"Agent says: Choosing first available color '{color}' for node '{node_to_color}'.")
                return {'action': 'color', 'node': node_to_color, 'color': color}
        
        # If all colors are taken by neighbors, we are forced to create a conflict.
        chosen_color = visible_state['available_colors'][0]
        print(f"Agent says: Dead end! Forced to choose conflicting color '{chosen_color}' for '{node_to_color}'.")
        return {'action': 'color', 'node': node_to_color, 'color': chosen_color}
