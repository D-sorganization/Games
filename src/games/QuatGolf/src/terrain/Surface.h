#pragma once
/**
 * @file Surface.h
 * @brief Golf course surface types with physical properties.
 *
 * Each surface type defines how the ball interacts with it:
 * friction (rolling resistance), bounce (restitution), and
 * speed penalty (e.g., rough slows the ball).
 *
 * Design by Contract:
 *   - Invariant: friction in [0, 1], bounce in [0, 1]
 *   - Postcondition: from_height() always returns a valid surface
 */

#include <string>

namespace qg {
namespace terrain {

enum class SurfaceType {
    Tee,        // Short, manicured — low friction
    Fairway,    // Standard grass
    Rough,      // Tall grass — high friction, speed penalty
    DeepRough,  // Very tall — major speed penalty
    Sand,       // Bunker — high friction, low bounce
    Green,      // Putting surface — very low friction
    Water,      // Hazard — ball resets with penalty
    OutOfBounds, // Ball resets with penalty
    Count
};

struct SurfaceProps {
    SurfaceType type;
    float friction;     // Rolling friction coefficient [0, 1]
    float bounce;       // Restitution coefficient [0, 1]
    float speed_mult;   // Ball speed multiplier (1.0 = normal)
    float r, g, b;      // Render color

    const char* name() const {
        switch (type) {
            case SurfaceType::Tee:          return "Tee";
            case SurfaceType::Fairway:      return "Fairway";
            case SurfaceType::Rough:        return "Rough";
            case SurfaceType::DeepRough:    return "Deep Rough";
            case SurfaceType::Sand:         return "Sand";
            case SurfaceType::Green:        return "Green";
            case SurfaceType::Water:        return "Water";
            case SurfaceType::OutOfBounds:  return "OB";
            default:                        return "?";
        }
    }
};

/** Get physical properties for a surface type. */
inline SurfaceProps get_surface(SurfaceType type) {
    switch (type) {
        case SurfaceType::Tee:
            return {type, 0.08f, 0.5f, 1.0f,   0.35f, 0.75f, 0.30f};
        case SurfaceType::Fairway:
            return {type, 0.10f, 0.45f, 1.0f,  0.28f, 0.65f, 0.22f};
        case SurfaceType::Rough:
            return {type, 0.30f, 0.35f, 0.7f,  0.22f, 0.48f, 0.16f};
        case SurfaceType::DeepRough:
            return {type, 0.50f, 0.25f, 0.4f,  0.16f, 0.36f, 0.12f};
        case SurfaceType::Sand:
            return {type, 0.60f, 0.15f, 0.5f,  0.90f, 0.82f, 0.60f};
        case SurfaceType::Green:
            return {type, 0.04f, 0.40f, 1.0f,  0.22f, 0.78f, 0.30f};
        case SurfaceType::Water:
            return {type, 1.00f, 0.00f, 0.0f,  0.15f, 0.35f, 0.70f};
        case SurfaceType::OutOfBounds:
        default:
            return {type, 0.50f, 0.30f, 0.5f,  0.40f, 0.35f, 0.30f};
    }
}

} // namespace terrain
} // namespace qg
