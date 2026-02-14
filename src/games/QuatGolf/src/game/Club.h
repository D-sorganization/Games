#pragma once
/**
 * @file Club.h
 * @brief Golf club definitions with launch parameters.
 *
 * Each club has a loft angle and power that determine launch velocity.
 * Higher loft = more height, less distance.
 */

#include "math/Vec3.h"

#include <cmath>
#include <string>

namespace qg {
namespace game {

struct Club {
    const char* name;
    float loft_deg;    // Loft angle in degrees
    float max_speed;   // Max ball speed (m/s) at full power
    float backspin;    // Default backspin (rad/s)
    int key;           // Keyboard key (1-9)

    /** Compute launch velocity from aim direction and power [0, 1]. */
    qe::math::Vec3 launch_velocity(const qe::math::Vec3& aim_dir, float power) const {
        float loft_rad = loft_deg * 3.14159f / 180.0f;
        float speed = max_speed * power;

        // Horizontal component
        float h_speed = speed * std::cos(loft_rad);
        // Vertical component
        float v_speed = speed * std::sin(loft_rad);

        qe::math::Vec3 horizontal = qe::math::Vec3(aim_dir.x, 0, aim_dir.z).normalized();
        return horizontal * h_speed + qe::math::Vec3(0, v_speed, 0);
    }

    /** Compute default spin vector (backspin around lateral axis). */
    qe::math::Vec3 default_spin(const qe::math::Vec3& aim_dir) const {
        qe::math::Vec3 horizontal = qe::math::Vec3(aim_dir.x, 0, aim_dir.z).normalized();
        // Spin axis is perpendicular to aim direction (lateral)
        qe::math::Vec3 spin_axis = qe::math::Vec3::up().cross(horizontal);
        return spin_axis * backspin;
    }
};

/** Standard club set. */
inline const Club CLUBS[] = {
    {"Driver",    10.5f, 73.0f, 50.0f,  1},
    {"3 Wood",    15.0f, 67.0f, 60.0f,  2},
    {"5 Iron",    27.0f, 56.0f, 90.0f,  3},
    {"7 Iron",    34.0f, 49.0f, 110.0f, 4},
    {"9 Iron",    41.0f, 42.0f, 130.0f, 5},
    {"PW",        46.0f, 38.0f, 140.0f, 6},
    {"SW",        56.0f, 30.0f, 150.0f, 7},
    {"LW",        60.0f, 25.0f, 160.0f, 8},
    {"Putter",     3.0f, 10.0f,   5.0f, 9},
};
constexpr int NUM_CLUBS = 9;

} // namespace game
} // namespace qg
