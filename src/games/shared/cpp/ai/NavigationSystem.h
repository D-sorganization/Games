#pragma once

#include "math/Vec3.h"
#include <vector>
#include <algorithm>
#include <cmath>

namespace qe {
namespace ai {

// Simple grid-based graph or waypoint system for now, as full NavMesh is complex.
// Let's implement a simple A* on a 2D grid overlaying the terrain.

struct Node {
    int x, z;
    float world_x, world_z;
    bool walkable = true;
    std::vector<Node*> neighbors;
    
    // A* data
    float g = 0, h = 0, f = 0;
    Node* parent = nullptr;
    int search_id = 0;
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
                Node& n = nodes[z * width + x];
                n.x = x; n.z = z;
                n.world_x = (x - width/2.0f) * scale; // Centered
                n.world_z = (z - depth/2.0f) * scale;
                n.walkable = true; // Assume flat for now, or check heightmap
            }
        }
        
        // Connect neighbors (4-way)
        for (int z = 0; z < depth; ++z) {
            for (int x = 0; x < width; ++x) {
                Node* n = &nodes[z * width + x];
                if (x > 0) n->neighbors.push_back(&nodes[z * width + (x-1)]);
                if (x < width-1) n->neighbors.push_back(&nodes[z * width + (x+1)]);
                if (z > 0) n->neighbors.push_back(&nodes[(z-1) * width + x]);
                if (z < depth-1) n->neighbors.push_back(&nodes[(z+1) * width + x]);
            }
        }
    }
    
    void mark_obstacle(float x, float z, float radius) {
        // Find nodes within radius and mark unwalkable
        // Simple circle check
        for (auto& n : nodes) {
            float dx = n.world_x - x;
            float dz = n.world_z - z;
            if (dx*dx + dz*dz < radius*radius) {
                n.walkable = false;
            }
        }
    }
    
    Node* get_node(float x, float z) {
        int gx = static_cast<int>(x / scale + width/2.0f);
        int gz = static_cast<int>(z / scale + depth/2.0f);
        if (gx >= 0 && gx < width && gz >= 0 && gz < depth) {
            return &nodes[gz * width + gx];
        }
        return nullptr;
    }

    std::vector<math::Vec3> find_path(const math::Vec3& start, const math::Vec3& end) {
        current_search_id++;
        Node* start_node = get_node(start.x, start.z);
        Node* end_node = get_node(end.x, end.z);

        if (!start_node || !end_node || !start_node->walkable || !end_node->walkable) return {};
        if (start_node == end_node) return {end};

        std::vector<Node*> open_set;
        open_set.push_back(start_node);

        start_node->g = 0;
        start_node->h = std::sqrt(std::pow(start_node->x - end_node->x, 2) + std::pow(start_node->z - end_node->z, 2));
        start_node->f = start_node->g + start_node->h;
        start_node->parent = nullptr;
        start_node->search_id = current_search_id;

        while (!open_set.empty()) {
            // Sort by F (lazy)
            std::sort(open_set.begin(), open_set.end(), [](Node* a, Node* b) { return a->f < b->f; });
            Node* current = open_set.front();
            open_set.erase(open_set.begin());

            if (current == end_node) {
                // Reconstruct
                std::vector<math::Vec3> path;
                Node* curr = end_node;
                while (curr) {
                    path.push_back({curr->world_x, 0, curr->world_z}); // Y ignored
                    curr = curr->parent;
                }
                std::reverse(path.begin(), path.end());
                return path;
            }

            for (Node* neighbor : current->neighbors) {
                if (!neighbor->walkable) continue;
                
                // If not visited in this search, reset
                if (neighbor->search_id != current_search_id) {
                    neighbor->g = 1e9f;
                    neighbor->search_id = current_search_id;
                    neighbor->parent = nullptr;
                }

                float tentative_g = current->g + 1.0f; // Uniform cost
                if (tentative_g < neighbor->g) {
                    neighbor->parent = current;
                    neighbor->g = tentative_g;
                    neighbor->h = std::sqrt(std::pow(neighbor->x - end_node->x, 2) + std::pow(neighbor->z - end_node->z, 2));
                    neighbor->f = neighbor->g + neighbor->h;
                    
                    // Add to open if not present (simple check: parent change implies re-eval)
                    bool in_open = false;
                    for (auto* n : open_set) if (n == neighbor) { in_open = true; break; }
                    if (!in_open) open_set.push_back(neighbor);
                }
            }
        }
        
        return {}; // No path
    }
};

} // namespace ai
} // namespace qe
