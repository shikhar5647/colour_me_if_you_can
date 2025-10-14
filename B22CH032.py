from collections import deque, defaultdict
import copy

class CSP_AGENT:
    """
    Elite CSP Agent for Graph Coloring with Partial Observability
    Features: Lookahead planning, backtracking detection, optimal path finding, and predictive exploration
    """
    def __init__(self, initial_state):
        """Initialize the agent with advanced memory and CSP structures"""
        print("Elite CSP Agent (B22CH032) initialized.")
        
        # Graph knowledge storage
        self.all_nodes = set()
        self.all_edges = set()
        self.adjacency = defaultdict(set)
        
        # CSP state
        self.node_colors = {}
        self.domains = {}
        self.available_colors = []
        
        # Movement and exploration tracking
        self.uncolored_nodes = set()
        self.visited_nodes = set()
        self.move_history = []
        
        # Advanced planning
        self.current_position = None
        self.pre_colored = {}
        self.coloring_order = []  # Planned coloring sequence
        self.graph_fully_explored = False
        
        # Backtracking detection
        self.last_assignment = {}  # Track previous color assignments
        
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
                # Detect pre-colored nodes
                if node not in self.visited_nodes and node not in self.node_colors:
                    self.pre_colored[node] = color
                
                self.node_colors[node] = color
                if node in self.uncolored_nodes:
                    self.uncolored_nodes.discard(node)
                
                # Update domains of neighbors
                self._propagate_constraints(node, color)
    
    def _propagate_constraints(self, node, color):
        """Advanced constraint propagation with arc consistency"""
        for neighbor in self.adjacency[node]:
            if neighbor not in self.node_colors:
                if neighbor in self.domains:
                    self.domains[neighbor].discard(color)
                    
                    # AC-3 style propagation: if domain becomes singleton, propagate further
                    if len(self.domains[neighbor]) == 1:
                        only_color = list(self.domains[neighbor])[0]
                        # Check if this would cause conflicts
                        self._check_singleton_viability(neighbor, only_color)
    
    def _check_singleton_viability(self, node, color):
        """Check if a forced color assignment is viable"""
        for neighbor in self.adjacency[node]:
            if neighbor in self.node_colors and self.node_colors[neighbor] == color:
                # Conflict detected - need to be careful
                return False
        return True
    
    def _calculate_node_priority(self, node):
        """Calculate priority score for node selection (lower is better)"""
        domain_size = len(self.domains.get(node, self.available_colors))
        degree = len(self.adjacency.get(node, []))
        
        # Count uncolored neighbors (future constraint potential)
        uncolored_neighbors = sum(1 for n in self.adjacency.get(node, []) 
                                 if n not in self.node_colors)
        
        # Prefer nodes with: small domain, high degree, many uncolored neighbors
        priority = (domain_size * 1000) - (degree * 100) - (uncolored_neighbors * 50)
        return priority
    
    def _find_optimal_next_target(self, visible_nodes):
        """Find the absolute best node to visit next using comprehensive analysis"""
        # Separate visible uncolored and non-visible uncolored
        visible_uncolored = [n for n in visible_nodes if n in self.uncolored_nodes]
        
        if visible_uncolored:
            # Among visible, pick most constrained
            visible_uncolored.sort(key=self._calculate_node_priority)
            return visible_uncolored[0], True  # True means it's visible
        
        # No uncolored visible - need to navigate to non-visible uncolored
        known_uncolored = list(self.uncolored_nodes)
        if known_uncolored:
            known_uncolored.sort(key=self._calculate_node_priority)
            return known_uncolored[0], False  # False means need to navigate
        
        return None, False
    
    def _bfs_shortest_path(self, start, goal, consider_colored=True):
        """Find shortest path from start to goal"""
        if start == goal:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self.adjacency[current]:
                if neighbor in visited:
                    continue
                    
                # Allow navigation through all known nodes
                if neighbor not in self.all_nodes:
                    continue
                
                new_path = path + [neighbor]
                if neighbor == goal:
                    return new_path
                
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        
        return None
    
    def _is_fully_explored(self):
        """Heuristic to determine if we've likely seen the whole graph"""
        # If all known nodes are colored and we haven't discovered new nodes recently
        if not self.uncolored_nodes:
            return True
        
        # If we have a well-connected component and reasonable coverage
        if len(self.visited_nodes) >= len(self.all_nodes) * 0.8:
            return True
            
        return False
    
    def _predict_conflicts(self, node, color):
        """Predict if assigning this color will cause future conflicts"""
        conflict_score = 0
        
        for neighbor in self.adjacency[node]:
            if neighbor not in self.node_colors:
                # Check if removing this color would over-constrain neighbor
                neighbor_domain = self.domains.get(neighbor, set(self.available_colors))
                if color in neighbor_domain:
                    remaining = len(neighbor_domain) - 1
                    if remaining <= 1:
                        conflict_score += 10  # High penalty for over-constraining
                    else:
                        conflict_score += 1
        
        return conflict_score
    
    def get_next_move(self, visible_state):
        """Decide where to move next using elite exploration strategy"""
        self._update_knowledge(visible_state)
        self.visited_nodes.add(self.current_position)
        
        visible_nodes = set(visible_state['visible_graph']['nodes'])
        
        # If current node is uncolored, stay here (we'll color it next)
        if self.current_position in self.uncolored_nodes:
            print(f"Agent: Staying at uncolored node '{self.current_position}'")
            return {'action': 'move', 'node': self.current_position}
        
        # Find optimal next target
        target, is_visible = self._find_optimal_next_target(visible_nodes)
        
        if target:
            if is_visible:
                # Target is visible - go directly
                print(f"Agent: Moving to high-priority target '{target}' (priority: {self._calculate_node_priority(target)})")
                self.move_history.append(target)
                return {'action': 'move', 'node': target}
            else:
                # Target not visible - find path
                path = self._bfs_shortest_path(self.current_position, target)
                
                if path and len(path) > 1:
                    next_node = path[1]
                    
                    # Prefer uncolored intermediate nodes if available
                    if next_node not in self.uncolored_nodes:
                        # Check if there's an uncolored visible alternative
                        uncolored_visible = [n for n in visible_nodes if n in self.uncolored_nodes]
                        if uncolored_visible:
                            next_node = min(uncolored_visible, key=self._calculate_node_priority)
                    
                    print(f"Agent: Navigating toward '{target}' via '{next_node}'")
                    self.move_history.append(next_node)
                    return {'action': 'move', 'node': next_node}
        
        # Fallback: explore any unvisited visible node
        unvisited_visible = [n for n in visible_nodes if n not in self.visited_nodes]
        if unvisited_visible:
            target = unvisited_visible[0]
            print(f"Agent: Exploring unvisited node '{target}'")
            self.move_history.append(target)
            return {'action': 'move', 'node': target}
        
        # Last resort: stay put
        print(f"Agent: Staying at '{self.current_position}' (exploration complete)")
        return {'action': 'move', 'node': self.current_position}
    
    def get_color_for_node(self, node_to_color, visible_state):
        """Choose optimal color using advanced CSP heuristics and lookahead"""
        self._update_knowledge(visible_state)
        
        # Handle pre-colored nodes
        if node_to_color in self.pre_colored:
            color = self.pre_colored[node_to_color]
            print(f"Agent: Keeping pre-colored node '{node_to_color}' as '{color}'")
            self.node_colors[node_to_color] = color
            self.uncolored_nodes.discard(node_to_color)
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
        
        if valid_colors:
            # Advanced color selection with conflict prediction
            color_scores = []
            
            for color in valid_colors:
                # Calculate multiple metrics
                constraint_count = sum(1 for n in self.adjacency[node_to_color] 
                                     if n not in self.node_colors and 
                                     color in self.domains.get(n, set()))
                
                conflict_score = self._predict_conflicts(node_to_color, color)
                
                # Calculate how many neighbors would still have options
                future_flexibility = 0
                for neighbor in self.adjacency[node_to_color]:
                    if neighbor not in self.node_colors:
                        neighbor_domain = self.domains.get(neighbor, set(self.available_colors))
                        remaining = len(neighbor_domain - {color})
                        future_flexibility += remaining
                
                # Composite score: minimize constraints, minimize conflicts, maximize flexibility
                total_score = (constraint_count * 10) + conflict_score - (future_flexibility * 5)
                color_scores.append((total_score, color))
            
            # Choose color with best score (lowest)
            color_scores.sort()
            best_color = color_scores[0][1]
            
            print(f"Agent: Coloring '{node_to_color}' with optimized color '{best_color}' (score: {color_scores[0][0]})")
            
            # Update internal state
            self.last_assignment[node_to_color] = best_color
            self.node_colors[node_to_color] = best_color
            self.uncolored_nodes.discard(node_to_color)
            self._propagate_constraints(node_to_color, best_color)
            
            return {'action': 'color', 'node': node_to_color, 'color': best_color}
        
        # Emergency fallback (should rarely happen)
        fallback_color = self.available_colors[0]
        print(f"Agent: WARNING - Forced to use potentially conflicting color '{fallback_color}' for '{node_to_color}'")
        
        self.last_assignment[node_to_color] = fallback_color
        self.node_colors[node_to_color] = fallback_color
        self.uncolored_nodes.discard(node_to_color)
        
        return {'action': 'color', 'node': node_to_color, 'color': fallback_color}