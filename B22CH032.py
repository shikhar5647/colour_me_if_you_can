from collections import deque, defaultdict
import copy

class CSP_AGENT:
    """
    CSP Agent for Graph Coloring with Partial Observability
    Uses intelligent exploration, constraint propagation, and backtracking with heuristics
    """
    def __init__(self, initial_state):
        """Initialize the agent with memory and CSP structures"""
        print("CSP Agent initialized.")
        
        # Graph knowledge storage
        self.all_nodes = set()
        self.all_edges = set()
        self.adjacency = defaultdict(set)
        
        # CSP state
        self.node_colors = {}
        self.domains = {}
        self.available_colors = []
        
        # Movement tracking
        self.uncolored_nodes = set()
        self.visited_nodes = set()
        self.exploration_queue = deque()
        
        # Strategic planning
        self.current_position = None
        self.pre_colored = {}
        
        # Initialize with first observation
        self._update_knowledge(initial_state)
        
    def _update_knowledge(self, visible_state):
        """Update internal graph knowledge from current observation"""
        self.current_position = visible_state['current_node']
        self.available_colors = visible_state['available_colors']
        
        # Add visible nodes
        for node in visible_state['visible_graph']['nodes']:
            if node not in self.all_nodes:
                self.all_nodes.add(node)
                self.uncolored_nodes.add(node)
                self.domains[node] = set(self.available_colors)
        
        # Add visible edges and build adjacency
        for edge in visible_state['visible_graph']['edges']:
            u, v = edge[0], edge[1]
            edge_tuple = tuple(sorted([u, v]))
            if edge_tuple not in self.all_edges:
                self.all_edges.add(edge_tuple)
                self.adjacency[u].add(v)
                self.adjacency[v].add(u)
        
        # Update coloring information
        for node, color in visible_state['node_colors'].items():
            if color is not None:
                self.node_colors[node] = color
                if node in self.uncolored_nodes:
                    self.uncolored_nodes.discard(node)
                
                # If this is a pre-colored node (colored but we didn't color it)
                if node not in self.visited_nodes and color is not None:
                    self.pre_colored[node] = color
                
                # Update domains of neighbors
                self._propagate_constraints(node, color)
    
    def _propagate_constraints(self, node, color):
        """Forward checking: remove assigned color from neighbors' domains"""
        for neighbor in self.adjacency[node]:
            if neighbor in self.domains and neighbor not in self.node_colors:
                self.domains[neighbor].discard(color)
    
    def _restore_domain(self, node, color):
        """Restore a color to a node's domain (for backtracking)"""
        if node in self.domains and node not in self.node_colors:
            # Only restore if no adjacent colored node uses this color
            can_restore = True
            for neighbor in self.adjacency[node]:
                if neighbor in self.node_colors and self.node_colors[neighbor] == color:
                    can_restore = False
                    break
            if can_restore:
                self.domains[node].add(color)
    
    def _find_most_constrained_uncolored(self, visible_nodes):
        """MRV heuristic: find uncolored node with smallest domain among visible nodes"""
        candidates = [n for n in visible_nodes if n in self.uncolored_nodes]
        if not candidates:
            return None
        
        # Sort by domain size (smallest first), then by degree (highest first)
        def priority(node):
            domain_size = len(self.domains.get(node, self.available_colors))
            degree = len(self.adjacency[node])
            return (domain_size, -degree)
        
        candidates.sort(key=priority)
        return candidates[0]
    
    def _find_exploration_target(self):
        """Find the best node to explore next using intelligent heuristics"""
        # Priority 1: Uncolored nodes we can see or have seen
        known_uncolored = [n for n in self.uncolored_nodes if n in self.all_nodes]
        
        if not known_uncolored:
            return None
        
        # Choose node with most constrained domain or highest degree
        def exploration_priority(node):
            domain_size = len(self.domains.get(node, self.available_colors))
            degree = len(self.adjacency[node])
            # Prefer nodes with small domains and high connectivity
            return (domain_size, -degree)
        
        known_uncolored.sort(key=exploration_priority)
        return known_uncolored[0]
    
    def _bfs_path(self, start, goal, allowed_nodes):
        """Find shortest path from start to goal using only allowed nodes"""
        if start == goal:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self.adjacency[current]:
                if neighbor in visited or neighbor not in allowed_nodes:
                    continue
                
                new_path = path + [neighbor]
                if neighbor == goal:
                    return new_path
                
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        
        return None
    
    def get_next_move(self, visible_state):
        """Decide where to move next using intelligent exploration"""
        self._update_knowledge(visible_state)
        self.visited_nodes.add(self.current_position)
        
        visible_nodes = set(visible_state['visible_graph']['nodes'])
        
        # Strategy 1: Move to most constrained uncolored visible node
        target = self._find_most_constrained_uncolored(visible_nodes)
        
        if target:
            print(f"Agent: Moving to constrained node '{target}'")
            return {'action': 'move', 'node': target}
        
        # Strategy 2: If all visible are colored, find next exploration target
        exploration_target = self._find_exploration_target()
        
        if exploration_target:
            # Try to find path to target through visible nodes
            path = self._bfs_path(self.current_position, exploration_target, visible_nodes)
            
            if path and len(path) > 1:
                next_node = path[1]
                print(f"Agent: Moving toward exploration target '{exploration_target}' via '{next_node}'")
                return {'action': 'move', 'node': next_node}
            
            # If target is visible, go there directly
            if exploration_target in visible_nodes:
                print(f"Agent: Moving to exploration target '{exploration_target}'")
                return {'action': 'move', 'node': exploration_target}
        
        # Strategy 3: Move to any uncolored visible node
        uncolored_visible = [n for n in visible_nodes if n in self.uncolored_nodes]
        if uncolored_visible:
            target = uncolored_visible[0]
            print(f"Agent: Moving to uncolored visible node '{target}'")
            return {'action': 'move', 'node': target}
        
        # Strategy 4: Stay put if nowhere else to go
        print(f"Agent: Staying at '{self.current_position}'")
        return {'action': 'move', 'node': self.current_position}
    
    def get_color_for_node(self, node_to_color, visible_state):
        """Choose optimal color using CSP heuristics"""
        self._update_knowledge(visible_state)
        
        # Don't color pre-colored nodes
        if node_to_color in self.pre_colored:
            color = self.pre_colored[node_to_color]
            print(f"Agent: Keeping pre-colored node '{node_to_color}' as '{color}'")
            return {'action': 'color', 'node': node_to_color, 'color': color}
        
        # Get colors used by neighbors
        neighbor_colors = set()
        for neighbor in self.adjacency[node_to_color]:
            if neighbor in self.node_colors:
                neighbor_colors.add(self.node_colors[neighbor])
        
        # Get available colors from domain
        available = self.domains.get(node_to_color, set(self.available_colors))
        valid_colors = [c for c in available if c not in neighbor_colors]
        
        # If no valid colors in domain, use any color not used by neighbors
        if not valid_colors:
            valid_colors = [c for c in self.available_colors if c not in neighbor_colors]
        
        # Choose color using Least Constraining Value heuristic
        if valid_colors:
            # Count how many neighbors would be constrained by each color
            def constraining_count(color):
                count = 0
                for neighbor in self.adjacency[node_to_color]:
                    if neighbor not in self.node_colors:
                        # Check if this color is in neighbor's domain
                        if color in self.domains.get(neighbor, set()):
                            count += 1
                return count
            
            # Choose color that constrains fewest neighbors
            best_color = min(valid_colors, key=constraining_count)
            print(f"Agent: Coloring '{node_to_color}' with optimal color '{best_color}'")
            
            # Update internal state
            self.node_colors[node_to_color] = best_color
            self.uncolored_nodes.discard(node_to_color)
            self._propagate_constraints(node_to_color, best_color)
            
            return {'action': 'color', 'node': node_to_color, 'color': best_color}
        
        # Emergency: no valid colors (shouldn't happen with proper CSP)
        fallback_color = self.available_colors[0]
        print(f"Agent: WARNING - Forced to use conflicting color '{fallback_color}' for '{node_to_color}'")
        
        self.node_colors[node_to_color] = fallback_color
        self.uncolored_nodes.discard(node_to_color)
        
        return {'action': 'color', 'node': node_to_color, 'color': fallback_color}