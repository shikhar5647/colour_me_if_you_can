
# # from collections import defaultdict, deque
# # import random

# # class CSP_AGENT:
# #     """
# #     Improved CSP agent for partial-observability graph coloring.
# #     - Persistent memory of discovered graph and assignments
# #     - BFS-based movement to nearest uncolored visible node
# #     - Forward-checking + LCV for coloring decisions
# #     """

# #     def __init__(self, initial_state):
# #         # initialize known graph & adjacency
# #         self.known_nodes = set(initial_state['visible_graph']['nodes'])
# #         self.known_edges = set()
# #         self.adjacency = defaultdict(set)
# #         for edge in initial_state['visible_graph']['edges']:
# #             e = tuple(edge)
# #             self.known_edges.add(tuple(sorted(e)))
# #             u, v = e
# #             self.adjacency[u].add(v)
# #             self.adjacency[v].add(u)

# #         # colors and assignments
# #         self.available_colors = list(initial_state.get('available_colors',
# #                                                        initial_state.get('colors', ["Red","Green","Blue"])))
# #         # copy any pre-known colors (node_colors may be partial)
# #         self.node_colors = dict(initial_state.get('node_colors', {}))

# #         # agent state
# #         self.current_node = initial_state['current_node']
# #         self.visited_nodes = set([self.current_node])
# #         self.uncolored_nodes = {n for n in self.known_nodes if self.node_colors.get(n) is None}

# #         print("CSP_AGENT initialized. start:", self.current_node)

# #     # -------------------------
# #     # Knowledge update helpers
# #     # -------------------------
# #     def update_knowledge(self, visible_state):
# #         # Add nodes
# #         for n in visible_state['visible_graph']['nodes']:
# #             if n not in self.known_nodes:
# #                 self.known_nodes.add(n)
# #                 # ensure adjacency entry exists
# #                 _ = self.adjacency[n]

# #         # Add edges
# #         for edge in visible_state['visible_graph']['edges']:
# #             u, v = edge
# #             et = tuple(sorted((u, v)))
# #             if et not in self.known_edges:
# #                 self.known_edges.add(et)
# #                 self.adjacency[u].add(v)
# #                 self.adjacency[v].add(u)

# #         # Update any node colors reported by environment
# #         for n, c in visible_state.get('node_colors', {}).items():
# #             if c is not None:
# #                 self.node_colors[n] = c

# #         # update current node & visited
# #         self.current_node = visible_state['current_node']
# #         self.visited_nodes.add(self.current_node)

# #         # recompute uncolored_nodes
# #         self.uncolored_nodes = {n for n in self.known_nodes if self.node_colors.get(n) is None}

# #     # -------------------------
# #     # Domain & heuristics
# #     # -------------------------
# #     def get_domain(self, node):
# #         """Return legal colors for node based on current node_colors."""
# #         # defensive
# #         if node not in self.known_nodes:
# #             return list(self.available_colors)

# #         if self.node_colors.get(node) is not None:
# #             return [self.node_colors[node]]

# #         forbidden = {self.node_colors[n] for n in self.adjacency[node] if self.node_colors.get(n) is not None}
# #         return [c for c in self.available_colors if c not in forbidden]

# #     def mrv_value(self, node):
# #         return len(self.get_domain(node))

# #     def degree(self, node):
# #         return len(self.adjacency[node])

# #     def count_uncolored_neighbors(self, node):
# #         return sum(1 for nb in self.adjacency[node] if self.node_colors.get(nb) is None)

# #     def is_consistent(self, node, color):
# #         for nb in self.adjacency[node]:
# #             if self.node_colors.get(nb) == color:
# #                 return False
# #         return True

# #     def forward_checking_simulate(self, node, color):
# #         """
# #         Simulate assigning color to node and check forward-checking:
# #         each uncolored neighbor must have at least one legal color left.
# #         """
# #         for nb in self.adjacency[node]:
# #             if self.node_colors.get(nb) is None:
# #                 # neighbor domain after forbidding 'color'
# #                 dom = [c for c in self.get_domain(nb) if c != color]
# #                 if not dom:
# #                     return False
# #         return True

# #     # -------------------------
# #     # Movement: BFS to nearest uncolored visible node
# #     # -------------------------
# #     def find_next_step_to_nearest_uncolored(self, visible_state):
# #         visible_nodes = set(visible_state['visible_graph']['nodes'])
# #         # collect visible uncolored nodes
# #         dests = [n for n in visible_nodes if self.node_colors.get(n) is None]
# #         if not dests:
# #             return None

# #         # BFS from current node over visible nodes only
# #         start = self.current_node
# #         queue = deque([(start, [start])])
# #         seen = {start}
# #         while queue:
# #             node, path = queue.popleft()
# #             if node in dests:
# #                 # return next hop
# #                 if len(path) >= 2:
# #                     return path[1]
# #                 return node
# #             for nb in self.adjacency[node]:
# #                 if nb in seen:
# #                     continue
# #                 if nb not in visible_nodes:
# #                     continue
# #                 seen.add(nb)
# #                 queue.append((nb, path + [nb]))

# #         # if no path (disconnected in visible subgraph), pick nearest dest by simple heuristic: MRV then degree
# #         dests_sorted = sorted(dests, key=lambda n: (self.mrv_value(n), -self.count_uncolored_neighbors(n)))
# #         return dests_sorted[0]

# #     # -------------------------
# #     # Node selection heuristics (for when we stay and color)
# #     # -------------------------
# #     def select_best_uncolored_visible(self, visible_state):
# #         visible_nodes = set(visible_state['visible_graph']['nodes'])
# #         candidates = [n for n in visible_nodes if self.node_colors.get(n) is None]
# #         if not candidates:
# #             return None
# #         # score: MRV primary, then more uncolored neighbors, then degree (higher better)
# #         def score(n):
# #             return (self.mrv_value(n), -self.count_uncolored_neighbors(n), -self.degree(n))
# #         return min(candidates, key=score)

# #     # -------------------------
# #     # Action: move decision
# #     # -------------------------
# #     def get_next_move(self, visible_state):
# #         """
# #         Prefer to stay and color current node if it's uncolored.
# #         Otherwise BFS to nearest visible uncolored node.
# #         If none, explore by moving to a visible colored neighbor not recently visited.
# #         """
# #         self.update_knowledge(visible_state)
# #         current = self.current_node

# #         # If current node is uncolored, stay (color it)
# #         if self.node_colors.get(current) is None:
# #             # stay to color
# #             # print(f"Agent: staying to color {current}")
# #             return {'action': 'move', 'node': current}

# #         # else move towards nearest visible uncolored node
# #         next_step = self.find_next_step_to_nearest_uncolored(visible_state)
# #         if next_step:
# #             # print(f"Agent: moving towards {next_step}")
# #             self.current_node = next_step
# #             return {'action': 'move', 'node': next_step}

# #         # No visible uncolored nodes -> explore. prefer visible colored neighbor not visited
# #         visible_nodes = set(visible_state['visible_graph']['nodes'])
# #         colored_neighbors = [n for n in visible_nodes if n != current and self.node_colors.get(n) is not None]
# #         unvisited = [n for n in colored_neighbors if n not in self.visited_nodes]
# #         if unvisited:
# #             choice = random.choice(unvisited)
# #             self.current_node = choice
# #             return {'action': 'move', 'node': choice}
# #         if colored_neighbors:
# #             choice = random.choice(colored_neighbors)
# #             self.current_node = choice
# #             return {'action': 'move', 'node': choice}

# #         # nothing else, stay
# #         return {'action': 'move', 'node': current}

# #     # -------------------------
# #     # Action: color decision
# #     # -------------------------
# #     def get_color_for_node(self, node_to_color, visible_state):
# #         """
# #         Choose color using forward checking + LCV and persist assignment.
# #         """
# #         self.update_knowledge(visible_state)

# #         # Defensive: ensure node is known
# #         if node_to_color not in self.known_nodes:
# #             self.known_nodes.add(node_to_color)

# #         domain = self.get_domain(node_to_color)
# #         if not domain:
# #             # forced conflict: pick a color anyway
# #             chosen = self.available_colors[0]
# #             self.node_colors[node_to_color] = chosen
# #             self.visited_nodes.add(node_to_color)
# #             self.uncolored_nodes.discard(node_to_color)
# #             return {'action': 'color', 'node': node_to_color, 'color': chosen}

# #         # LCV: prefer color that preserves most options for neighbors
# #         best_color = None
# #         best_score = -1
# #         for color in domain:
# #             if not self.is_consistent(node_to_color, color):
# #                 continue
# #             if not self.forward_checking_simulate(node_to_color, color):
# #                 continue
# #             # compute neighbors_preserved: how many neighbor domain options remain if we chose 'color'
# #             preserved = 0
# #             for nb in self.adjacency[node_to_color]:
# #                 if self.node_colors.get(nb) is None:
# #                     nb_dom = self.get_domain(nb)
# #                     if color in nb_dom:
# #                         # if we pick color, neighbor loses that option; we want to preserve neighbors' options,
# #                         # so count remaining size after removal (higher is better)
# #                         preserved += (len(nb_dom) - 1)
# #                     else:
# #                         preserved += len(nb_dom)
# #             # We want maximize preserved (higher better)
# #             if preserved > best_score or best_color is None:
# #                 best_score = preserved
# #                 best_color = color

# #         if best_color is None:
# #             # either LCV filtering removed everything or all colors equal; pick domain[0]
# #             best_color = domain[0]

# #         # Persist the assignment
# #         self.node_colors[node_to_color] = best_color
# #         self.visited_nodes.add(node_to_color)
# #         self.uncolored_nodes.discard(node_to_color)

# #         # Return the action
# #         return {'action': 'color', 'node': node_to_color, 'color': best_color}



# from collections import defaultdict, deque
# import random

# class CSP_AGENT:
#     """
#     A CSP-based agent for the Graph Coloring Game under partial observability.
#     It uses:
#       - Persistent knowledge of discovered graph structure and colors
#       - BFS for movement to nearest uncolored visible node
#       - Forward checking and LCV (Least Constraining Value) for coloring
#     """

#     def __init__(self, initial_state):
#         # --- Initialize known graph state ---
#         self.known_nodes = set(initial_state['visible_graph']['nodes'])
#         self.known_edges = set()
#         self.adjacency = defaultdict(set)

#         for edge in initial_state['visible_graph']['edges']:
#             u, v = edge
#             e = tuple(sorted((u, v)))
#             self.known_edges.add(e)
#             self.adjacency[u].add(v)
#             self.adjacency[v].add(u)

#         # --- Colors and assignments ---
#         self.available_colors = list(initial_state.get('available_colors',
#             initial_state.get('colors', ["Red", "Green", "Blue"])))
#         self.node_colors = dict(initial_state.get('node_colors', {}))

#         # --- Agent’s internal state ---
#         self.current_node = initial_state['current_node']
#         self.visited_nodes = {self.current_node}
#         self.uncolored_nodes = {n for n in self.known_nodes if self.node_colors.get(n) is None}

#     # ==========================================================
#     # KNOWLEDGE UPDATE
#     # ==========================================================
#     def update_knowledge(self, visible_state):
#         """Update internal knowledge from the visible state."""
#         for n in visible_state['visible_graph']['nodes']:
#             self.known_nodes.add(n)
#             _ = self.adjacency[n]

#         for edge in visible_state['visible_graph']['edges']:
#             u, v = edge
#             e = tuple(sorted((u, v)))
#             if e not in self.known_edges:
#                 self.known_edges.add(e)
#                 self.adjacency[u].add(v)
#                 self.adjacency[v].add(u)

#         for n, c in visible_state.get('node_colors', {}).items():
#             if c is not None:
#                 self.node_colors[n] = c

#         self.current_node = visible_state['current_node']
#         self.visited_nodes.add(self.current_node)
#         self.uncolored_nodes = {n for n in self.known_nodes if self.node_colors.get(n) is None}

#     # ==========================================================
#     # HELPER FUNCTIONS
#     # ==========================================================
#     def get_domain(self, node):
#         """Return all valid colors for a node given current assignments."""
#         if self.node_colors.get(node) is not None:
#             return [self.node_colors[node]]

#         forbidden = {self.node_colors[n] for n in self.adjacency[node]
#                      if self.node_colors.get(n) is not None}
#         return [c for c in self.available_colors if c not in forbidden]

#     def mrv(self, node):
#         return len(self.get_domain(node))

#     def degree(self, node):
#         return len(self.adjacency[node])

#     def uncolored_neighbors(self, node):
#         return sum(1 for nb in self.adjacency[node] if self.node_colors.get(nb) is None)

#     def is_consistent(self, node, color):
#         return all(self.node_colors.get(nb) != color for nb in self.adjacency[node])

#     def forward_check(self, node, color):
#         """Ensure forward-checking validity for this color assignment."""
#         for nb in self.adjacency[node]:
#             if self.node_colors.get(nb) is None:
#                 remaining = [c for c in self.get_domain(nb) if c != color]
#                 if not remaining:
#                     return False
#         return True

#     # ==========================================================
#     # MOVEMENT STRATEGY
#     # ==========================================================
#     def find_next_step_to_uncolored(self, visible_state):
#         """Find the next move using BFS to nearest visible uncolored node."""
#         visible_nodes = set(visible_state['visible_graph']['nodes'])
#         dests = [n for n in visible_nodes if self.node_colors.get(n) is None]
#         if not dests:
#             return None

#         start = self.current_node
#         queue = deque([(start, [start])])
#         seen = {start}

#         while queue:
#             node, path = queue.popleft()
#             if node in dests:
#                 return path[1] if len(path) >= 2 else node
#             for nb in self.adjacency[node]:
#                 if nb not in seen and nb in visible_nodes:
#                     seen.add(nb)
#                     queue.append((nb, path + [nb]))

#         # fallback: pick visible uncolored node with smallest domain (MRV)
#         dests_sorted = sorted(dests, key=lambda n: (self.mrv(n), -self.uncolored_neighbors(n)))
#         return dests_sorted[0]

#     # ==========================================================
#     # MOVE DECISION
#     # ==========================================================
#     def get_next_move(self, visible_state):
#         self.update_knowledge(visible_state)
#         current = self.current_node

#         # Stay and color current node if uncolored
#         if self.node_colors.get(current) is None:
#             return {'action': 'move', 'node': current}

#         # Move to nearest visible uncolored node
#         next_node = self.find_next_step_to_uncolored(visible_state)
#         if next_node:
#             self.current_node = next_node
#             return {'action': 'move', 'node': next_node}

#         # Otherwise, explore visible colored neighbors
#         visible_nodes = set(visible_state['visible_graph']['nodes'])
#         neighbors = [n for n in visible_nodes if n != current]
#         unvisited = [n for n in neighbors if n not in self.visited_nodes]

#         if unvisited:
#             choice = random.choice(unvisited)
#             self.current_node = choice
#             return {'action': 'move', 'node': choice}

#         # fallback: random visible node
#         if neighbors:
#             choice = random.choice(neighbors)
#             self.current_node = choice
#             return {'action': 'move', 'node': choice}

#         # nothing else, stay
#         return {'action': 'move', 'node': current}

#     # ==========================================================
#     # COLOR DECISION
#     # ==========================================================
#     def get_color_for_node(self, node_to_color, visible_state):
#         self.update_knowledge(visible_state)
#         domain = self.get_domain(node_to_color)

#         if not domain:
#             chosen = random.choice(self.available_colors)
#             self.node_colors[node_to_color] = chosen
#             return {'action': 'color', 'node': node_to_color, 'color': chosen}

#         # Choose least constraining color
#         best_color, best_score = None, -1
#         for color in domain:
#             if not self.is_consistent(node_to_color, color):
#                 continue
#             if not self.forward_check(node_to_color, color):
#                 continue

#             preserved = 0
#             for nb in self.adjacency[node_to_color]:
#                 if self.node_colors.get(nb) is None:
#                     nb_domain = self.get_domain(nb)
#                     preserved += len(nb_domain) - (1 if color in nb_domain else 0)
#             if preserved > best_score:
#                 best_score = preserved
#                 best_color = color

#         if best_color is None:
#             best_color = domain[0]

#         self.node_colors[node_to_color] = best_color
#         self.uncolored_nodes.discard(node_to_color)
#         return {'action': 'color', 'node': node_to_color, 'color': best_color}



from collections import defaultdict, deque
import random

class B22EE088:
    """
    Fixed CSP agent for partial-observability graph coloring.
    Improvements:
    - Safe color assignment
    - BFS movement to nearest uncolored node
    - Avoid cycles using recent_nodes memory
    - Forward checking on all known neighbors
    """
    def __init__(self, initial_state):
        # Initialize known graph
        self.known_nodes = set(initial_state['visible_graph']['nodes'])
        self.known_edges = set()
        self.adjacency = defaultdict(set)
        for edge in initial_state['visible_graph']['edges']:
            u, v = edge
            et = tuple(sorted((u, v)))
            self.known_edges.add(et)
            self.adjacency[u].add(v)
            self.adjacency[v].add(u)

        # Colors & assignments
        self.available_colors = list(initial_state.get('available_colors', initial_state.get('colors', ["Red","Green","Blue"])))
        self.node_colors = dict(initial_state.get('node_colors', {}))
        for n, c in initial_state.get('pre_colored', {}).items():
            self.node_colors[n] = c

        # Agent state
        self.current_node = initial_state['current_node']
        self.visited_nodes = set([self.current_node])
        self.uncolored_nodes = {n for n in self.known_nodes if self.node_colors.get(n) is None}

        # Movement memory to avoid cycles
        self.recent_nodes = deque(maxlen=10)

        print("CSP_AGENT initialized. start:", self.current_node)

    # -----------------------------
    # Knowledge update
    # -----------------------------
    def update_knowledge(self, visible_state):
        for n in visible_state['visible_graph']['nodes']:
            if n not in self.known_nodes:
                self.known_nodes.add(n)
                _ = self.adjacency[n]
        for edge in visible_state['visible_graph']['edges']:
            u, v = edge
            et = tuple(sorted((u, v)))
            if et not in self.known_edges:
                self.known_edges.add(et)
                self.adjacency[u].add(v)
                self.adjacency[v].add(u)
        for n, c in visible_state.get('node_colors', {}).items():
            if c is not None:
                self.node_colors[n] = c
        self.current_node = visible_state['current_node']
        self.visited_nodes.add(self.current_node)
        self.uncolored_nodes = {n for n in self.known_nodes if self.node_colors.get(n) is None}

    # -----------------------------
    # Domain & heuristics
    # -----------------------------
    def get_domain(self, node):
        if node not in self.known_nodes:
            return list(self.available_colors)
        if self.node_colors.get(node) is not None:
            return [self.node_colors[node]]
        forbidden = {self.node_colors[n] for n in self.adjacency[node] if self.node_colors.get(n) is not None}
        return [c for c in self.available_colors if c not in forbidden]

    def is_consistent(self, node, color):
        return all(self.node_colors.get(nb) != color for nb in self.adjacency[node])

    def forward_checking_simulate(self, node, color):
        """Check all neighbors have at least one color left."""
        for nb in self.adjacency[node]:
            if self.node_colors.get(nb) is None:
                dom = [c for c in self.available_colors if c != color and self.is_consistent(nb, c)]
                if not dom:
                    return False
        return True

    # -----------------------------
    # Movement: BFS to nearest uncolored visible node
    # -----------------------------
    def find_next_step_to_nearest_uncolored(self, visible_state):
        visible_nodes = set(visible_state['visible_graph']['nodes'])
        dests = [n for n in visible_nodes if self.node_colors.get(n) is None]
        if not dests:
            return None
        start = self.current_node
        queue = deque([(start, [start])])
        seen = {start}
        while queue:
            node, path = queue.popleft()
            if node in dests:
                return path[1] if len(path) >= 2 else node
            for nb in self.adjacency[node]:
                if nb not in seen and nb in visible_nodes:
                    seen.add(nb)
                    queue.append((nb, path + [nb]))
        dests_sorted = sorted(dests, key=lambda n: (len(self.get_domain(n)), -sum(1 for nb in self.adjacency[n] if self.node_colors.get(nb) is None)))
        return dests_sorted[0]

    # -----------------------------
    # Move action
    # -----------------------------
    def get_next_move(self, visible_state):
        self.update_knowledge(visible_state)
        current = self.current_node
        self.recent_nodes.append(current)

        # Stay to color if uncolored
        if self.node_colors.get(current) is None:
            return {'action': 'move', 'node': current}

        # Move towards nearest uncolored node
        next_step = self.find_next_step_to_nearest_uncolored(visible_state)
        if next_step:
            self.current_node = next_step
            return {'action': 'move', 'node': next_step}

        # Explore: pick colored neighbor not in recent_nodes
        neighbors = [n for n in self.adjacency[current] if n != current]
        unvisited = [n for n in neighbors if n not in self.recent_nodes]
        if unvisited:
            choice = random.choice(unvisited)
        elif neighbors:
            choice = random.choice(neighbors)
        else:
            choice = current
        self.current_node = choice
        return {'action': 'move', 'node': choice}

    # -----------------------------
    # Color action
    # -----------------------------
    def get_color_for_node(self, node_to_color, visible_state):
        self.update_knowledge(visible_state)
        domain = self.get_domain(node_to_color)

        # Safe color choice
        best_color = None
        for color in domain:
            if self.is_consistent(node_to_color, color) and self.forward_checking_simulate(node_to_color, color):
                best_color = color
                break
        if best_color is None:
            best_color = domain[0] if domain else self.available_colors[0]

        # Assign color
        self.node_colors[node_to_color] = best_color
        self.visited_nodes.add(node_to_color)
        self.uncolored_nodes.discard(node_to_color)
        return {'action': 'color', 'node': node_to_color, 'color': best_color}
