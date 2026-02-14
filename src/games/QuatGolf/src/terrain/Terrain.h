#pragma once
/**
 * @file Terrain.h
 * @brief Heightmap-based golf course terrain with surface types.
 *
 * Generates a renderable mesh from a 2D heightmap. Each cell has:
 *   - Height (Y value from the heightmap)
 *   - Surface type (fairway, rough, sand, etc.)
 *   - Normal (computed from neighbours for smooth shading)
 *
 * The heightmap is procedurally generated for now. Future: load from image.
 *
 * Design by Contract:
 *   - Precondition: width, depth >= 2
 *   - Invariant: heights_ and surfaces_ are width * depth
 *   - Postcondition: mesh vertices match heightmap dimensions
 */

#include "Surface.h"
#include "math/Vec3.h"
#include "renderer/Mesh.h"

#include <algorithm>
#include <cmath>
#include <vector>

namespace qg {
namespace terrain {

class Terrain {
public:
    int width  = 0;  // Grid cells in X
    int depth  = 0;  // Grid cells in Z
    float cell_size = 1.0f;  // World units per cell

    /** Build terrain mesh from internal heightmap + surface data. */
    void build_mesh() {
        if (width < 2 || depth < 2) return;

        std::vector<qe::renderer::Vertex> verts;
        std::vector<unsigned> indices;
        verts.reserve(width * depth);
        indices.reserve((width - 1) * (depth - 1) * 6);

        // Vertices
        for (int z = 0; z < depth; ++z) {
            for (int x = 0; x < width; ++x) {
                qe::renderer::Vertex v;
                float wx = (x - width / 2.0f) * cell_size;
                float wz = (z - depth / 2.0f) * cell_size;
                float wy = height_at(x, z);

                v.position[0] = wx;
                v.position[1] = wy;
                v.position[2] = wz;

                // Normal from finite differences
                auto n = normal_at(x, z);
                v.normal[0] = n.x;
                v.normal[1] = n.y;
                v.normal[2] = n.z;

                // Color from surface type
                auto surf = get_surface(surface_at(x, z));
                v.color[0] = surf.r;
                v.color[1] = surf.g;
                v.color[2] = surf.b;

                // UV for potential texture
                v.uv[0] = static_cast<float>(x) / (width - 1);
                v.uv[1] = static_cast<float>(z) / (depth - 1);

                verts.push_back(v);
            }
        }

        // Indices (two triangles per quad)
        for (int z = 0; z < depth - 1; ++z) {
            for (int x = 0; x < width - 1; ++x) {
                unsigned tl = z * width + x;
                unsigned tr = tl + 1;
                unsigned bl = (z + 1) * width + x;
                unsigned br = bl + 1;

                indices.push_back(tl);
                indices.push_back(bl);
                indices.push_back(tr);

                indices.push_back(tr);
                indices.push_back(bl);
                indices.push_back(br);
            }
        }

        mesh.upload(verts, indices);
    }

    /** Get height at grid coordinates (clamped). */
    float height_at(int x, int z) const {
        x = std::clamp(x, 0, width - 1);
        z = std::clamp(z, 0, depth - 1);
        return heights_[z * width + x];
    }

    /** Get height at world coordinates (bilinear interpolation). */
    float height_at_world(float wx, float wz) const {
        float gx = wx / cell_size + width / 2.0f;
        float gz = wz / cell_size + depth / 2.0f;

        int x0 = static_cast<int>(std::floor(gx));
        int z0 = static_cast<int>(std::floor(gz));
        float fx = gx - x0;
        float fz = gz - z0;

        float h00 = height_at(x0, z0);
        float h10 = height_at(x0 + 1, z0);
        float h01 = height_at(x0, z0 + 1);
        float h11 = height_at(x0 + 1, z0 + 1);

        float h0 = h00 + (h10 - h00) * fx;
        float h1 = h01 + (h11 - h01) * fx;
        return h0 + (h1 - h0) * fz;
    }

    /** Get surface normal at world position. */
    qe::math::Vec3 normal_at_world(float wx, float wz) const {
        float gx = wx / cell_size + width / 2.0f;
        float gz = wz / cell_size + depth / 2.0f;
        int x = static_cast<int>(std::round(gx));
        int z = static_cast<int>(std::round(gz));
        return normal_at(x, z);
    }

    /** Get surface type at world coordinates. */
    SurfaceType surface_at_world(float wx, float wz) const {
        float gx = wx / cell_size + width / 2.0f;
        float gz = wz / cell_size + depth / 2.0f;
        int x = static_cast<int>(std::round(gx));
        int z = static_cast<int>(std::round(gz));
        return surface_at(x, z);
    }

    /** Get surface type at grid coordinates (clamped). */
    SurfaceType surface_at(int x, int z) const {
        x = std::clamp(x, 0, width - 1);
        z = std::clamp(z, 0, depth - 1);
        return surfaces_[z * width + x];
    }

    /** Compute normal from height differences. */
    qe::math::Vec3 normal_at(int x, int z) const {
        float hL = height_at(x - 1, z);
        float hR = height_at(x + 1, z);
        float hD = height_at(x, z - 1);
        float hU = height_at(x, z + 1);
        return qe::math::Vec3(hL - hR, 2.0f * cell_size, hD - hU).normalized();
    }

    /** Set heightmap data directly. */
    void set_data(int w, int d, float cs,
                  std::vector<float> heights,
                  std::vector<SurfaceType> surfaces) {
        width = w;
        depth = d;
        cell_size = cs;
        heights_ = std::move(heights);
        surfaces_ = std::move(surfaces);
    }

    void draw() const { mesh.draw(); }
    void destroy() { mesh.destroy(); }

    qe::renderer::Mesh mesh;

private:
    std::vector<float> heights_;
    std::vector<SurfaceType> surfaces_;
};

} // namespace terrain
} // namespace qg
