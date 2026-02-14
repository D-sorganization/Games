#pragma once
/**
 * @file CourseBuilder.h
 * @brief Stamps hole definitions onto terrain heightmap + surface data.
 *
 * Takes a Hole definition and a Terrain, and paints:
 *   - Tee box surface
 *   - Fairway strip (following control points)
 *   - Rough/deep rough borders
 *   - Bunker depressions with sand surface
 *   - Green surface with subtle slope
 *   - Water hazard (flat, low area)
 *   - Pin marker position
 *
 * Also generates gentle rolling hills for the base terrain.
 */

#include "Hole.h"
#include "../terrain/Surface.h"
#include "../terrain/Terrain.h"
#include "math/Vec3.h"

#include <cmath>
#include <vector>

namespace qg {
namespace course {

class CourseBuilder {
public:
    /** Generate base terrain with gentle rolling hills. */
    static void generate_base(terrain::Terrain& t, int w, int d, float cs) {
        std::vector<float> heights(w * d, 0.0f);
        std::vector<terrain::SurfaceType> surfaces(w * d, terrain::SurfaceType::Rough);

        // Gentle rolling hills using layered sine waves
        for (int z = 0; z < d; ++z) {
            for (int x = 0; x < w; ++x) {
                float wx = static_cast<float>(x) / w;
                float wz = static_cast<float>(z) / d;

                float h = 0.0f;
                // Large rolling hills
                h += std::sin(wx * 3.14159f * 2) * 0.8f;
                h += std::cos(wz * 3.14159f * 3) * 0.5f;
                // Medium bumps
                h += std::sin(wx * 7 + wz * 5) * 0.3f;
                h += std::cos(wx * 11 - wz * 3) * 0.2f;
                // Fine detail
                h += std::sin(wx * 23 + wz * 17) * 0.05f;

                heights[z * w + x] = h;
            }
        }

        t.set_data(w, d, cs, std::move(heights), std::move(surfaces));
    }

    /** Stamp a hole onto the terrain. */
    static void stamp_hole(terrain::Terrain& t, const Hole& hole) {
        stamp_fairway(t, hole);
        stamp_tee(t, hole.tee);
        stamp_green(t, hole.green);
        for (const auto& b : hole.bunkers) stamp_bunker(t, b);
        if (hole.has_water) stamp_water(t, hole.water_center, hole.water_radius);
    }

    /** Build a default 3-hole course for testing. */
    static std::vector<Hole> default_course() {
        using namespace qe::math;
        std::vector<Hole> holes;

        // Hole 1 — Par 4, straight, 380 yards
        {
            Hole h;
            h.number = 1; h.par = 4; h.yards = 380;
            h.tee = {Vec3(0, 0, 60), 3, 4};
            h.green = {Vec3(0, 0, -60), 7, Vec3(0, 0, -60), 2, 0};
            h.fairway = {
                {Vec3(0, 0, 50), 10},
                {Vec3(0, 0, 20), 14},
                {Vec3(0, 0, -10), 14},
                {Vec3(0, 0, -40), 12},
                {Vec3(0, 0, -55), 10}
            };
            h.bunkers = {
                {Vec3(-10, 0, -45), 4, 0.4f},
                {Vec3(8, 0, -55), 3, 0.3f}
            };
            holes.push_back(h);
        }

        // Hole 2 — Par 3, short, 160 yards
        {
            Hole h;
            h.number = 2; h.par = 3; h.yards = 160;
            h.tee = {Vec3(40, 0, 60), 3, 4};
            h.green = {Vec3(40, 0, 10), 6, Vec3(40, 0, 10), 3, 1.2f};
            h.fairway = {
                {Vec3(40, 0, 50), 8},
                {Vec3(40, 0, 30), 10},
                {Vec3(40, 0, 15), 8}
            };
            h.bunkers = {
                {Vec3(34, 0, 8), 3, 0.3f},
                {Vec3(46, 0, 12), 3, 0.3f},
                {Vec3(40, 0, 4), 2, 0.2f}
            };
            h.has_water = true;
            h.water_center = Vec3(48, 0, 30);
            h.water_radius = 6;
            holes.push_back(h);
        }

        // Hole 3 — Par 5, dogleg left, 520 yards
        {
            Hole h;
            h.number = 3; h.par = 5; h.yards = 520;
            h.tee = {Vec3(-40, 0, 60), 3, 4};
            h.green = {Vec3(-60, 0, -50), 8, Vec3(-60, 0, -50), 2, 0.8f};
            h.fairway = {
                {Vec3(-40, 0, 50), 12},
                {Vec3(-40, 0, 20), 14},
                {Vec3(-45, 0, -5), 14},   // Start dogleg
                {Vec3(-52, 0, -25), 13},
                {Vec3(-58, 0, -40), 11},
                {Vec3(-60, 0, -48), 10}
            };
            h.bunkers = {
                {Vec3(-35, 0, 0), 5, 0.4f},   // Fairway bunker at dogleg
                {Vec3(-65, 0, -45), 3, 0.3f},
                {Vec3(-55, 0, -55), 3, 0.3f}
            };
            holes.push_back(h);
        }

        return holes;
    }

private:
    /** Grid coordinates from world position. */
    static void world_to_grid(const terrain::Terrain& t, float wx, float wz,
                               int& gx, int& gz) {
        gx = static_cast<int>(wx / t.cell_size + t.width / 2.0f);
        gz = static_cast<int>(wz / t.cell_size + t.depth / 2.0f);
    }

    /** Paint a circular patch of surface type. */
    static void paint_circle(terrain::Terrain& t,
                              std::vector<terrain::SurfaceType>& surfaces,
                              std::vector<float>& heights,
                              float cx, float cz, float radius,
                              terrain::SurfaceType surface,
                              float height_offset = 0.0f,
                              bool flatten = false) {
        int gx0, gz0;
        world_to_grid(t, cx - radius, cz - radius, gx0, gz0);
        int gx1, gz1;
        world_to_grid(t, cx + radius, cz + radius, gx1, gz1);

        gx0 = std::max(0, gx0);
        gz0 = std::max(0, gz0);
        gx1 = std::min(t.width - 1, gx1);
        gz1 = std::min(t.depth - 1, gz1);

        for (int z = gz0; z <= gz1; ++z) {
            for (int x = gx0; x <= gx1; ++x) {
                float wx = (x - t.width / 2.0f) * t.cell_size;
                float wz = (z - t.depth / 2.0f) * t.cell_size;
                float dx = wx - cx;
                float dz = wz - cz;
                float dist = std::sqrt(dx * dx + dz * dz);

                if (dist <= radius) {
                    int idx = z * t.width + x;
                    surfaces[idx] = surface;
                    if (flatten) {
                        // Smooth transition
                        float blend = dist / radius;
                        float target = t.height_at(x, z) + height_offset;
                        heights[idx] = heights[idx] * blend + target * (1 - blend) +
                                       height_offset;
                    } else if (height_offset != 0.0f) {
                        float blend = 1.0f - (dist / radius);
                        heights[idx] += height_offset * blend;
                    }
                }
            }
        }
    }

    /** Stamp fairway strip following control points. */
    static void stamp_fairway(terrain::Terrain& t, const Hole& hole) {
        auto& heights = const_cast<std::vector<float>&>(
            *reinterpret_cast<const std::vector<float>*>(
                reinterpret_cast<const char*>(&t) +
                sizeof(int) * 2 + sizeof(float) +
                sizeof(qe::renderer::Mesh)));
        // NOTE: This is hacky — we need Terrain to expose mutable access.
        // For now use a simpler approach: rebuild after stamping.

        // Get mutable data (we'll rebuild the mesh after)
        std::vector<float> h(t.width * t.depth);
        std::vector<terrain::SurfaceType> s(t.width * t.depth);

        for (int z = 0; z < t.depth; ++z) {
            for (int x = 0; x < t.width; ++x) {
                h[z * t.width + x] = t.height_at(x, z);
                s[z * t.width + x] = t.surface_at(x, z);
            }
        }

        // Paint fairway along control points
        for (size_t i = 0; i + 1 < hole.fairway.size(); ++i) {
            auto& p0 = hole.fairway[i];
            auto& p1 = hole.fairway[i + 1];
            float len = p0.position.distance_to(p1.position);
            int steps = static_cast<int>(len / 0.5f) + 1;

            for (int s_idx = 0; s_idx <= steps; ++s_idx) {
                float t_val = static_cast<float>(s_idx) / steps;
                auto pos = p0.position.lerp(p1.position, t_val);
                float width = p0.width + (p1.width - p0.width) * t_val;

                // Paint fairway
                paint_circle(t, s, h, pos.x, pos.z, width * 0.5f,
                             terrain::SurfaceType::Fairway, -0.05f, false);
                // Paint rough border
                paint_circle(t, s, h, pos.x, pos.z, width * 0.5f + 5.0f,
                             terrain::SurfaceType::Rough, 0, false);
            }
        }

        // Repaint fairway over rough (rough was painted with bigger radius)
        for (size_t i = 0; i + 1 < hole.fairway.size(); ++i) {
            auto& p0 = hole.fairway[i];
            auto& p1 = hole.fairway[i + 1];
            float len = p0.position.distance_to(p1.position);
            int steps = static_cast<int>(len / 0.5f) + 1;

            for (int s_idx = 0; s_idx <= steps; ++s_idx) {
                float t_val = static_cast<float>(s_idx) / steps;
                auto pos = p0.position.lerp(p1.position, t_val);
                float width = p0.width + (p1.width - p0.width) * t_val;

                paint_circle(t, s, h, pos.x, pos.z, width * 0.5f,
                             terrain::SurfaceType::Fairway, 0, false);
            }
        }

        t.set_data(t.width, t.depth, t.cell_size, std::move(h), std::move(s));
    }

    static void stamp_tee(terrain::Terrain& t, const TeeDef& tee) {
        std::vector<float> h(t.width * t.depth);
        std::vector<terrain::SurfaceType> s(t.width * t.depth);
        for (int z = 0; z < t.depth; ++z)
            for (int x = 0; x < t.width; ++x) {
                h[z * t.width + x] = t.height_at(x, z);
                s[z * t.width + x] = t.surface_at(x, z);
            }

        paint_circle(t, s, h, tee.position.x, tee.position.z,
                     std::max(tee.width, tee.depth),
                     terrain::SurfaceType::Tee, 0.1f, true);

        t.set_data(t.width, t.depth, t.cell_size, std::move(h), std::move(s));
    }

    static void stamp_green(terrain::Terrain& t, const GreenDef& green) {
        std::vector<float> h(t.width * t.depth);
        std::vector<terrain::SurfaceType> s(t.width * t.depth);
        for (int z = 0; z < t.depth; ++z)
            for (int x = 0; x < t.width; ++x) {
                h[z * t.width + x] = t.height_at(x, z);
                s[z * t.width + x] = t.surface_at(x, z);
            }

        // Green surface — slightly flattened with gentle slope
        paint_circle(t, s, h, green.center.x, green.center.z, green.radius,
                     terrain::SurfaceType::Green, 0, true);

        // Add slope if nonzero
        if (green.slope_angle > 0.01f) {
            int gx0, gz0, gx1, gz1;
            world_to_grid(t, green.center.x - green.radius,
                          green.center.z - green.radius, gx0, gz0);
            world_to_grid(t, green.center.x + green.radius,
                          green.center.z + green.radius, gx1, gz1);
            gx0 = std::max(0, gx0);
            gz0 = std::max(0, gz0);
            gx1 = std::min(t.width - 1, gx1);
            gz1 = std::min(t.depth - 1, gz1);

            float slope_rad = green.slope_angle * 3.14159f / 180.0f;
            float slope_dx = std::cos(green.slope_dir) * std::tan(slope_rad);
            float slope_dz = std::sin(green.slope_dir) * std::tan(slope_rad);

            for (int z = gz0; z <= gz1; ++z)
                for (int x = gx0; x <= gx1; ++x) {
                    float wx = (x - t.width / 2.0f) * t.cell_size - green.center.x;
                    float wz = (z - t.depth / 2.0f) * t.cell_size - green.center.z;
                    float dist = std::sqrt(wx * wx + wz * wz);
                    if (dist <= green.radius) {
                        h[z * t.width + x] += wx * slope_dx + wz * slope_dz;
                    }
                }
        }

        t.set_data(t.width, t.depth, t.cell_size, std::move(h), std::move(s));
    }

    static void stamp_bunker(terrain::Terrain& t, const Bunker& bunker) {
        std::vector<float> h(t.width * t.depth);
        std::vector<terrain::SurfaceType> s(t.width * t.depth);
        for (int z = 0; z < t.depth; ++z)
            for (int x = 0; x < t.width; ++x) {
                h[z * t.width + x] = t.height_at(x, z);
                s[z * t.width + x] = t.surface_at(x, z);
            }

        paint_circle(t, s, h, bunker.center.x, bunker.center.z, bunker.radius,
                     terrain::SurfaceType::Sand, -bunker.depth, true);

        t.set_data(t.width, t.depth, t.cell_size, std::move(h), std::move(s));
    }

    static void stamp_water(terrain::Terrain& t, qe::math::Vec3 center, float radius) {
        std::vector<float> h(t.width * t.depth);
        std::vector<terrain::SurfaceType> s(t.width * t.depth);
        for (int z = 0; z < t.depth; ++z)
            for (int x = 0; x < t.width; ++x) {
                h[z * t.width + x] = t.height_at(x, z);
                s[z * t.width + x] = t.surface_at(x, z);
            }

        paint_circle(t, s, h, center.x, center.z, radius,
                     terrain::SurfaceType::Water, -0.5f, true);

        t.set_data(t.width, t.depth, t.cell_size, std::move(h), std::move(s));
    }
};

} // namespace course
} // namespace qg
