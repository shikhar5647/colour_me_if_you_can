import random
from collections import deque, defaultdict

class B22CH032:
    """
    My CSP agent code 
    """
    def __init__(self, initial_state):
        print("B22CH032 CSP Agent Initialized.")
        # PERSISTENT STATE (Agent's Global Memory)
        self.all_nodes = set()
        self.adjacency = defaultdict(set)
        self.edges_seen = set()
        # CSP State
        self.available_colors = initial_state['available_colors']
        self.pre_colored = {} # Nodes whose color cannot be changed (fixed constraints)
        self.current_position = None
        # The single source of truth for the entire known graph's coloring
        # {node: color | None} - Best known valid assignment
        self.global_assignment = {}
        
        self._update_knowledge(initial_state)

    # 1. KNOWLEDGE MANAGEMENT AND SYNCHRONIZATION

    def _update_knowledge(self, visible_state):
        """Update graph knowledge from observation and synchronize state."""
        self.current_position = visible_state['current_node']
        
        # 1. Update Graph Structure (Nodes and Edges)
        for node in visible_state['visible_graph']['nodes']:
            if node not in self.all_nodes:
                self.all_nodes.add(node)
                # Initialize new node as uncolored
                self.global_assignment[node] = None 
                
        for u, v in visible_state['visible_graph']['edges']:
            edge_tuple = tuple(sorted([u, v]))
            if edge_tuple not in self.edges_seen:
                self.edges_seen.add(edge_tuple)
                self.adjacency[u].add(v)
                self.adjacency[v].add(u)

        # 2. Synchronize Colors with Game State
        for node, color in visible_state['node_colors'].items():
            if color is not None:
                # If a node appears colored in the game (either pre-colored or from a 
                # previous turn), update our memory to reflect the ground truth.
                self.global_assignment[node] = color
                # If it's a new fixed color, mark it as pre-colored to exclude from search variables.
                if node not in self.pre_colored and self.global_assignment.get(node) == color:
                    self.pre_colored[node] = color
            
            elif node in self.global_assignment and node not in self.pre_colored:
                 # If the game reports None, and it wasn't pre-colored, it's unassigned.
                 self.global_assignment[node] = None

    # 2. CSP HELPER FUNCTIONS (Consistency, Heuristics)
    def _get_available_colors(self, node, assignment):
        """Returns the set of colors consistent with the current assignment."""
        neighbor_colors = set()
        for neighbor in self.adjacency[node]:
            if neighbor in assignment and assignment[neighbor] is not None:
                neighbor_colors.add(assignment[neighbor])
        
        return [c for c in self.available_colors if c not in neighbor_colors]

    def _select_unassigned_variable(self, assignment, unassigned_nodes):
        """MRV with Degree Heuristic tie-breaker."""
        if not unassigned_nodes:
            return None
        best_node = None
        min_remaining_values = float('inf')
        max_degree = -1 
        
        for node in unassigned_nodes:
            # MRV: Remaining Legal Colors
            num_colors = len(self._get_available_colors(node, assignment))
            
            # Degree: Unassigned Neighbors
            degree = len([n for n in self.adjacency[node] if n in unassigned_nodes])

            # Selection Logic: Prioritize MRV, then Degree
            if num_colors < min_remaining_values:
                min_remaining_values = num_colors
                max_degree = degree
                best_node = node
            elif num_colors == min_remaining_values and degree > max_degree:
                max_degree = degree
                best_node = node
                
        return best_node

    def _order_domain_values(self, node, assignment, unassigned_nodes):
        """LCV heuristic."""
        available_colors = self._get_available_colors(node, assignment)
        if not available_colors:
            return []
        
        color_scores = []
        for color in available_colors:
            constraint_count = 0
            # Count how many choices this color eliminates for unassigned neighbors
            for neighbor in self.adjacency[node]:
                if neighbor in unassigned_nodes:
                    # Calculate domain size if 'color' is assigned to 'node'
                    temp_assignment = assignment.copy()
                    temp_assignment[node] = color
                    
                    # Count remaining legal colors for neighbor
                    remaining_options = len(self._get_available_colors(neighbor, temp_assignment))
                    
                    # The constraint is inversely proportional to the remaining options
                    constraint_count += remaining_options
            
            # LCV chooses the value that leaves the most options (highest score)
            color_scores.append((constraint_count, color))
            
        # Sort by constraint_count (descending) - choose least constraining value first
        color_scores.sort(key=lambda x: x[0], reverse=True)
        return [color for _, color in color_scores]

    # 3. CONSTRAINT PROPAGATION (AC-3)
    def _remove_inconsistent_values(self, X, Y, domains):
        """Makes arc (X, Y) consistent, part of AC-3."""
        removed = False
        domain_X = domains.get(X, set())
        domain_Y = domains.get(Y, set())
        
        for x in list(domain_X):
            # Check if there is *at least one* y in D(Y) that satisfies the constraint
            consistent_y_found = False
            for y in domain_Y:
                if x != y:
                    consistent_y_found = True
                    break
            
            if not consistent_y_found:
                domain_X.remove(x)
                removed = True
                
        domains[X] = domain_X
        return removed

    def _ac3_propagation(self, assignment, unassigned_nodes):
        """Runs the AC-3 algorithm to enforce arc consistency."""
        domains = {}
        for node in unassigned_nodes:
            # Initialize domain based on current partial assignment
            domains[node] = set(self._get_available_colors(node, assignment))

        queue = deque()
        # Initialize queue with all arcs between unassigned nodes
        for u in unassigned_nodes:
            for v in self.adjacency[u]:
                if v in unassigned_nodes and u != v:
                    queue.append((u, v))
        
        while queue:
            X, Y = queue.popleft()
            
            if self._remove_inconsistent_values(X, Y, domains):
                if not domains[X]:
                    return False, domains  # Failure: Domain emptied
                
                # Add all relevant arcs for reprocessing: (Z, X)
                for Z in self.adjacency[X]:
                    if Z != Y and Z in unassigned_nodes:
                        queue.append((Z, X))
                        
        return True, domains
    # 4. BACKTRACKING SEARCH (Fwd Check + Heuristics)
    def _backtrack_search_fwd_check(self, assignment, unassigned_nodes, domains):
        """Recursive backtracking search with Forward Checking and Heuristics."""
        
        if not unassigned_nodes:
            return assignment
        
        node = self._select_unassigned_variable(assignment, unassigned_nodes)

        # Get the ordered colors from the AC-3 pruned domains
        domain_values = [c for c in self._order_domain_values(node, assignment, unassigned_nodes) 
                         if c in domains[node]] 

        for color in domain_values:
            
            # 1. Assignment and Consistency Check (Consistency is guaranteed by LCV/MRV)
            assignment[node] = color
            new_unassigned = unassigned_nodes - {node}
            # 2. Forward Checking: Check if any unassigned neighbor's domain is emptied
            valid = True
            for neighbor in self.adjacency[node]:
                if neighbor in new_unassigned:
                    if not self._get_available_colors(neighbor, assignment):
                        valid = False
                        break
            
            if valid:
                # 3. Recurse
                result = self._backtrack_search_fwd_check(assignment, new_unassigned, domains)
                if result is not None:
                    return result
            
            # 4. Backtrack
            assignment[node] = None 
            
        return None

    # 5. GLOBAL PLANNING AND REPAIR
    def _plan_global_coloring(self):
        """Runs CSP with a repair strategy if the initial plan fails."""
        unassigned_vars = {n for n in self.all_nodes if n not in self.pre_colored and self.global_assignment.get(n) is None}
        # Keep a copy of the assignment to modify during the repair process
        assignment = self.global_assignment.copy()
        # Retry loop for repair
        for attempt in range(2): 
            print(f"Planning: Starting attempt {attempt + 1}. Unassigned: {len(unassigned_vars)}")
            # Step 1: Run AC-3 on the current state (prunes domains aggressively)
            ac3_ok, domains = self._ac3_propagation(assignment, unassigned_vars)
            
            if not ac3_ok:
                print("Planning: AC-3 detected an inevitable conflict early.")
                if attempt == 0: 
                    # If initial AC-3 fails, try repair by clearing a past assignment
                    pass
                else: 
                    # Repair failed, state is impossible.
                    return False
            # Step 2: Run the full search using the pruned domains
            result = self._backtrack_search_fwd_check(assignment.copy(), unassigned_vars, domains)
            if result:
                # SUCCESS
                self.global_assignment.update(result)
                print(f"Planning: Successfully updated global plan (Attempt {attempt+1}).")
                return True
            # Step 3: REPAIR STRATEGY (If search failed on the first attempt)
            if attempt == 0:
                print("Planning: Search failed. Attempting repair by clearing high-degree node...")
                # Find the assigned, non-pre-colored node with the highest degree.
                nodes_to_clear = [n for n in self.all_nodes if n not in self.pre_colored and assignment.get(n) is not None]
                if not nodes_to_clear:
                    # Nothing to clear, no way to fix the conflict
                    return False
                    
                # Heuristic: Clear the highest degree node (most constrained)
                node_to_clear = max(nodes_to_clear, key=lambda n: len(self.adjacency[n]))
                
                print(f"Planning: Clearing assignment of '{node_to_clear}' to enable repair.")
                
                # Clear its color and add it back to the unassigned set for the next attempt
                assignment[node_to_clear] = None
                unassigned_vars.add(node_to_clear)
            
        return False

    # 6. ACTION LOGIC
    def get_next_move(self, visible_state):
        """Intelligent movement heuristic."""
        self._update_knowledge(visible_state)
        
        uncolored_nodes = {n for n in self.all_nodes if self.global_assignment.get(n) is None}
        visible_nodes = set(visible_state['visible_graph']['nodes'])
        
        # 1. Stay at current position if uncolored (to color it this turn)
        if self.current_position in uncolored_nodes:
            return {'action': 'move', 'node': self.current_position}
        
        # 2. Move to an uncolored neighbor (within radius 1) - prioritize by constraint
        uncolored_neighbors = [n for n in visible_nodes if n in uncolored_nodes]
        if uncolored_neighbors:
            
            def move_priority(node):
                # Calculate MRV (lower is better)
                mrv = len(self._get_available_colors(node, self.global_assignment))
                
                # Calculate Degree Heuristic (higher is better)
                degree = len([n for n in self.adjacency[node] if n in uncolored_nodes])
                
                # Heuristic tuple: (MRV, -Degree) - Lower tuple is better (most constrained)
                return (mrv, -degree)

            # Find the best target among visible, uncolored nodes
            target = min(uncolored_neighbors, key=move_priority)
            return {'action': 'move', 'node': target}

        # 3. Navigate to closest uncolored node in known graph
        if uncolored_nodes:
            # Prioritize the most constrained uncolored node in the *entire* known graph
            target = self._select_unassigned_variable(self.global_assignment, uncolored_nodes)
            
            path = self._find_path(self.current_position, target)
            if path and len(path) > 1:
                next_node = path[1]
                # Ensure the next step is a visible node (which it must be if the path is found)
                if next_node in visible_nodes: 
                    return {'action': 'move', 'node': next_node}

        # 4. Explore a random visible neighbor to expand knowledge
        visible_neighbors = [n for n in visible_nodes if n != self.current_position]
        if visible_neighbors:
            target = random.choice(visible_neighbors)
            return {'action': 'move', 'node': target}
        
        # 5. Stay put (Fully colored or blocked)
        return {'action': 'move', 'node': self.current_position}

    def get_color_for_node(self, node_to_color, visible_state):
        """Color node using the result of the continuous global planning."""
        self._update_knowledge(visible_state)
        
        # 1. Check if pre-colored (Cannot re-color these)
        if node_to_color in self.pre_colored:
             color = self.pre_colored[node_to_color]
             return {'action': 'color', 'node': node_to_color, 'color': color}

        # 2. Execute Global Planning (This is the primary way to minimize reassignments)
        if not self._plan_global_coloring():
            print("Agent: Global plan failed. Forced to use local heuristic.")
        
        # 3. Use the result of the new consistent plan
        color = self.global_assignment.get(node_to_color)
        
        if color is not None:
            # The color is derived from a consistent global plan
            return {'action': 'color', 'node': node_to_color, 'color': color}
        
        # 4. Fallback (Should only happen if planning failed globally and 
        #    the node to color couldn't be assigned by the repair strategy)
        valid_colors = self._get_available_colors(node_to_color, self.global_assignment)
            
        if valid_colors:
            # Use LCV on the remaining valid options as a safer fallback
            lcv_order = self._order_domain_values(node_to_color, self.global_assignment, set())
            # Find the first color that is still valid based on the final assignment state
            chosen_color = next((c for c in lcv_order if c in valid_colors), self.available_colors[0])
            
            self.global_assignment[node_to_color] = chosen_color
            return {'action': 'color', 'node': node_to_color, 'color': chosen_color}
            
        # Absolute dead-end
        fallback = self.available_colors[0]
        self.global_assignment[node_to_color] = fallback
        return {'action': 'color', 'node': node_to_color, 'color': fallback}

    # 7. PATHFINDING HELPER    
    def _find_path(self, start, goal):
        """BFS to find shortest path in the known graph."""
        if start == goal:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self.adjacency[current]:
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    if neighbor == goal:
                        return new_path
                    
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))
        
        return None