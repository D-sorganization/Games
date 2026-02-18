#pragma once

#include "math/Vec3.h"
#include <algorithm>
#include <cmath>
#include <queue>
#include <vector>

namespace qe {
namespace ai {

// Grid-based A* pathfinding system.
// Uses a priority queue (min-heap) with lazy deletion for O(E log V)
// performance.

struct Node {
  int x, z;
  float world_x, world_z;
  bool walkable = true;
  std::vector<Node *> neighbors;

  // A* data
  float g = 0, h = 0, f = 0;
  Node *parent = nullptr;
  int search_id = 0;
  int closed_id = 0; // Tracks closed set per search (lazy deletion)
};

class NavigationSystem {
public:
  std::vector<Node> nodes;
  int width = 0, depth = 0;
  float scale = 1.0f;
  int current_search_id = 0;

  void init(int w, int d, float s) {
    width = w;
    depth = d;
    scale = s;
    nodes.resize(width * depth);

    // Grid setup
    for (int z = 0; z < depth; ++z) {
      for (int x = 0; x < width; ++x) {
        Node &n = nodes[z * width + x];
        n.x = x;
        n.z = z;
        n.world_x = (x - width / 2.0f) * scale; // Centered
        n.world_z = (z - depth / 2.0f) * scale;
        n.walkable = true; // Assume flat for now, or check heightmap
      }
    }

    // Connect neighbors (4-way)
    for (int z = 0; z < depth; ++z) {
      for (int x = 0; x < width; ++x) {
        Node *n = &nodes[z * width + x];
        if (x > 0)
          n->neighbors.push_back(&nodes[z * width + (x - 1)]);
        if (x < width - 1)
          n->neighbors.push_back(&nodes[z * width + (x + 1)]);
        if (z > 0)
          n->neighbors.push_back(&nodes[(z - 1) * width + x]);
        if (z < depth - 1)
          n->neighbors.push_back(&nodes[(z + 1) * width + x]);
      }
    }
  }

  void mark_obstacle(float x, float z, float radius) {
    // Find nodes within radius and mark unwalkable
    // Simple circle check
    for (auto &n : nodes) {
      float dx = n.world_x - x;
      float dz = n.world_z - z;
      if (dx * dx + dz * dz < radius * radius) {
        n.walkable = false;
      }
    }
  }

  Node *get_node(float x, float z) {
    int gx = static_cast<int>(x / scale + width / 2.0f);
    int gz = static_cast<int>(z / scale + depth / 2.0f);
    if (gx >= 0 && gx < width && gz >= 0 && gz < depth) {
      return &nodes[gz * width + gx];
    }
    return nullptr;
  }

  std::vector<math::Vec3> find_path(const math::Vec3 &start,
                                    const math::Vec3 &end) {
    current_search_id++;
    Node *start_node = get_node(start.x, start.z);
    Node *end_node = get_node(end.x, end.z);

    if (!start_node || !end_node || !start_node->walkable ||
        !end_node->walkable)
      return {};
    if (start_node == end_node)
      return {end};

    // Min-heap ordered by f-score (lowest first)
    auto cmp = [](Node *a, Node *b) { return a->f > b->f; };
    std::priority_queue<Node *, std::vector<Node *>, decltype(cmp)> open_pq(
        cmp);

    start_node->g = 0;
    float dx = static_cast<float>(start_node->x - end_node->x);
    float dz = static_cast<float>(start_node->z - end_node->z);
    start_node->h = std::sqrt(dx * dx + dz * dz);
    start_node->f = start_node->g + start_node->h;
    start_node->parent = nullptr;
    start_node->search_id = current_search_id;
    start_node->closed_id = 0;
    open_pq.push(start_node);

    while (!open_pq.empty()) {
      Node *current = open_pq.top();
      open_pq.pop();

      // Lazy deletion: skip nodes already in closed set
      if (current->closed_id == current_search_id)
        continue;
      current->closed_id = current_search_id;

      if (current == end_node) {
        // Reconstruct path
        std::vector<math::Vec3> path;
        Node *curr = end_node;
        while (curr) {
          path.push_back({curr->world_x, 0, curr->world_z});
          curr = curr->parent;
        }
        std::reverse(path.begin(), path.end());
        return path;
      }

      for (Node *neighbor : current->neighbors) {
        if (!neighbor->walkable)
          continue;

        // Initialize node for this search if first visit
        if (neighbor->search_id != current_search_id) {
          neighbor->g = 1e9f;
          neighbor->search_id = current_search_id;
          neighbor->closed_id = 0;
          neighbor->parent = nullptr;
        }

        // Skip already-closed nodes
        if (neighbor->closed_id == current_search_id)
          continue;

        float tentative_g = current->g + 1.0f;
        if (tentative_g < neighbor->g) {
          neighbor->parent = current;
          neighbor->g = tentative_g;
          float ndx = static_cast<float>(neighbor->x - end_node->x);
          float ndz = static_cast<float>(neighbor->z - end_node->z);
          neighbor->h = std::sqrt(ndx * ndx + ndz * ndz);
          neighbor->f = neighbor->g + neighbor->h;
          open_pq.push(
              neighbor); // Push new entry; stale entries skipped via closed_id
        }
      }
    }

    return {}; // No path found
  }
};

} // namespace ai
} // namespace qe
