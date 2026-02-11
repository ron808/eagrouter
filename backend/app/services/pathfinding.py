# a* pathfinding on the grid -- finds shortest routes while respecting blocked edges

import heapq
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models import Node, BlockedEdge


class PathfindingService:
    # uses manhattan distance as the a* heuristic and caches the graph so we don't reload it every time

    def __init__(self, db: Session):
        self.db = db
        self._nodes: Dict[int, Tuple[int, int]] = {}
        self._coord_to_node: Dict[Tuple[int, int], int] = {}
        self._blocked_edges: Set[Tuple[int, int]] = set()
        self._loaded = False

    def _load_grid(self):
        # lazy-loads the grid from the db on first use so we don't hit it unnecessarily
        if self._loaded:
            return

        nodes = self.db.query(Node).all()
        for node in nodes:
            self._nodes[node.id] = (node.x, node.y)
            self._coord_to_node[(node.x, node.y)] = node.id

        # blocked edges are bidirectional, so store both directions for easy lookup
        blocked = self.db.query(BlockedEdge).all()
        for edge in blocked:
            self._blocked_edges.add((edge.from_node_id, edge.to_node_id))
            self._blocked_edges.add((edge.to_node_id, edge.from_node_id))

        self._loaded = True

    def _get_neighbors(self, node_id: int) -> List[int]:
        # returns the 4 cardinal neighbors (up/down/left/right) that aren't blocked
        if node_id not in self._nodes:
            return []

        x, y = self._nodes[node_id]
        neighbors = []

        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy

            if (nx, ny) in self._coord_to_node:
                neighbor_id = self._coord_to_node[(nx, ny)]

                if (node_id, neighbor_id) not in self._blocked_edges:
                    neighbors.append(neighbor_id)

        return neighbors

    def _heuristic(self, node_id: int, goal_id: int) -> int:
        # manhattan distance -- good fit for a grid where you can only move in 4 directions
        if node_id not in self._nodes or goal_id not in self._nodes:
            return float('inf')

        x1, y1 = self._nodes[node_id]
        x2, y2 = self._nodes[goal_id]

        return abs(x1 - x2) + abs(y1 - y2)

    def find_path(self, start_id: int, goal_id: int) -> Optional[List[int]]:
        # classic a* search -- returns the list of node ids from start to goal, or None if no path exists
        self._load_grid()

        if start_id not in self._nodes or goal_id not in self._nodes:
            return None

        if start_id == goal_id:
            return [start_id]

        open_set = [(0, start_id)]
        came_from: Dict[int, int] = {}
        g_score: Dict[int, float] = {start_id: 0}
        f_score: Dict[int, float] = {start_id: self._heuristic(start_id, goal_id)}
        closed_set: Set[int] = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_id:
                return self._reconstruct_path(came_from, current)

            if current in closed_set:
                continue
            closed_set.add(current)

            for neighbor in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal_id)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None

    def _reconstruct_path(self, came_from: Dict[int, int], current: int) -> List[int]:
        # walks backwards through the came_from map to rebuild the full path
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def get_path_length(self, start_id: int, goal_id: int) -> Optional[int]:
        path = self.find_path(start_id, goal_id)
        if path is None:
            return None
        return len(path) - 1

    def get_node_coords(self, node_id: int) -> Optional[Tuple[int, int]]:
        self._load_grid()
        return self._nodes.get(node_id)
