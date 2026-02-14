#pragma once
/**
 * @file Hole.h
 * @brief Single golf hole definition — tee, fairway path, green, pin.
 *
 * A Hole is a pure data description. It doesn't own rendering resources.
 * The Course uses Hole data to stamp surfaces and heights into the terrain.
 */

#include "math/Vec3.h"

#include <string>
#include <vector>

namespace qg {
namespace course {

struct Bunker {
    qe::math::Vec3 center;
    float radius = 3.0f;
    float depth  = 0.3f;  // How far below terrain surface
};

struct GreenDef {
    qe::math::Vec3 center;
    float radius     = 8.0f;
    qe::math::Vec3 pin;  // Flag/hole position on green
    float slope_angle = 2.0f;  // Degrees of slope
    float slope_dir   = 0.0f;  // Direction of slope (radians)
};

struct TeeDef {
    qe::math::Vec3 position;
    float width  = 3.0f;
    float depth  = 4.0f;
};

/** Defines the fairway as a series of control points with width. */
struct FairwayPoint {
    qe::math::Vec3 position;
    float width = 12.0f;  // Fairway width at this point
};

struct Hole {
    int number    = 1;
    int par       = 4;
    float yards   = 380.0f;  // Tee to pin distance

    TeeDef tee;
    GreenDef green;
    std::vector<FairwayPoint> fairway;  // Control points along fairway
    std::vector<Bunker> bunkers;

    // Optional: water hazard
    bool has_water = false;
    qe::math::Vec3 water_center;
    float water_radius = 0.0f;

    /** Compute straight-line distance from tee to pin (meters). */
    float distance_m() const {
        return tee.position.distance_to(green.pin);
    }
};

} // namespace course
} // namespace qg
