import json
from collections import deque, defaultdict

class GraphColoringGame:
    def __init__(self, level_file):
        with open(level_file) as f:
            data = json.load(f)
        self.nodes = data["graph"]["nodes"]
        self.edges = data["graph"]["edges"]
        self.colors = data["colors"]
        self.visibility_radius = data["visibility_radius"]
        self.start_node = data["start_node"]
        self.pre_colored = data.get("pre_colored", {})
        
        self.adj = defaultdict(list)
        for u,v in self.edges:
            self.adj[u].append(v)
            self.adj[v].append(u)
        
        # node colors: start with pre_colored or None
        self.node_colors = {n:self.pre_colored.get(n, None) for n in self.nodes}
        
        # track backtracks/reassignments
        self.reassignments = 0
        self.moves = [self.start_node]
        
    def visible_subgraph(self, current_node):
        # This function will return nodes and edges visible from current_node within radius
        visited = set()
        queue = deque([(current_node,0)])
        vis_nodes = set()
        vis_edges = set()
        while queue:
            node, d = queue.popleft()
            if node in visited or d > self.visibility_radius:
                continue
            visited.add(node)
            vis_nodes.add(node)
            for neighbor in self.adj[node]:
                vis_edges.add(tuple(sorted([node,neighbor])))
                queue.append((neighbor,d+1))
        return list(vis_nodes), list(vis_edges)
    
    def assign_color(self, node, color):
        # will assign color, count backtracks/reassignments
        if self.node_colors[node] is not None and self.node_colors[node] != color:
            self.reassignments += 1
        self.node_colors[node] = color
    
    def is_valid_assignment(self, node, color):
        # check assignment violations
        for neighbor in self.adj[node]:
            if self.node_colors.get(neighbor) == color:
                return False
        return True
    
    def move_to_node(self, node):
        self.moves.append(node)
    
    def score(self):
        correct = all(self.node_colors[n] is not None for n in self.nodes)
        base = 100 if correct else 0
        return max(0, base - self.reassignments)
    
    def get_state(self, current_node):
        # Return visible subgraph and current node colors
        vis_nodes, vis_edges = self.visible_subgraph(current_node)
        vis_colors = {n:self.node_colors[n] for n in vis_nodes}
        return {
            "visible_nodes": vis_nodes,
            "visible_edges": vis_edges,
            "visible_colors": vis_colors
        }
    
    def summary(self):
        return {
            "node_colors": self.node_colors,
            "moves": self.moves,
            "reassignments": self.reassignments,
            "score": self.score()
        }
