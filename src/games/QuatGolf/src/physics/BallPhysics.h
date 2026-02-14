#pragma once
/**
 * @file BallPhysics.h
 * @brief Golf ball flight and terrain interaction physics.
 *
 * Physics model:
 *   - Flight: gravity + aerodynamic drag + lift (Magnus from spin)
 *   - Terrain contact: bounce (restitution * surface), rolling friction
 *   - Rolling: deceleration from surface friction, terrain slope
 *
 * Design by Contract:
 *   - Invariant: ball position always has a valid terrain height below it
 *   - Postcondition: after update(), speed >= 0
 *
 * Intentionally simple — no MuJoCo needed for golf ball dynamics.
 * For research-grade simulation, see UpstreamDrift's multi-physics engine.
 */

#include "../terrain/Surface.h"
#include "../terrain/Terrain.h"
#include "math/Vec3.h"

#include <algorithm>
#include <cmath>

namespace qg {
namespace physics {

/** Ball state — position, velocity, spin. */
struct BallState {
    qe::math::Vec3 position;
    qe::math::Vec3 velocity;
    qe::math::Vec3 spin;  // Angular velocity (rad/s) — for Magnus effect
    bool in_flight = false;
    bool rolling   = false;
    bool stopped   = false;
    bool in_water  = false;

    float speed() const { return velocity.length(); }
};

/** Physical constants for golf ball aerodynamics. */
struct BallConstants {
    float mass        = 0.04593f;  // kg (regulation golf ball)
    float radius      = 0.02135f;  // metres
    float area        = 0.001432f; // m² (cross-section)
    float drag_coeff  = 0.25f;     // Cd (dimpled ball)
    float lift_coeff  = 0.18f;     // Cl (Magnus effect)
    float air_density = 1.225f;    // kg/m³

    float gravity     = 9.81f;     // m/s²
    float min_speed   = 0.02f;     // Below this, ball stops (m/s)
    float bounce_loss = 0.15f;     // Additional energy loss on bounce

    // Wind
    qe::math::Vec3 wind{0, 0, 0};  // m/s
};

class BallPhysics {
public:
    BallConstants constants;

    /** Update ball state for one timestep. */
    void update(BallState& ball, const terrain::Terrain& terrain, float dt) {
        if (ball.stopped || ball.in_water) return;

        if (ball.in_flight) {
            update_flight(ball, dt);
            check_terrain_contact(ball, terrain);
        } else if (ball.rolling) {
            update_rolling(ball, terrain, dt);
        }
    }

    /** Launch ball with given velocity and spin. */
    void launch(BallState& ball, const qe::math::Vec3& velocity,
                const qe::math::Vec3& spin = {0, 0, 0}) {
        ball.velocity = velocity;
        ball.spin = spin;
        ball.in_flight = true;
        ball.rolling = false;
        ball.stopped = false;
        ball.in_water = false;
    }

private:
    /** Flight physics: gravity + drag + Magnus lift. */
    void update_flight(BallState& ball, float dt) {
        using qe::math::Vec3;

        Vec3 rel_vel = ball.velocity - constants.wind;
        float speed = rel_vel.length();
        if (speed < 0.001f) return;

        Vec3 drag_dir = rel_vel.normalized() * -1.0f;

        // Drag: F = 0.5 * rho * Cd * A * v²
        float drag_force = 0.5f * constants.air_density *
                           constants.drag_coeff * constants.area *
                           speed * speed;
        Vec3 drag_accel = drag_dir * (drag_force / constants.mass);

        // Magnus lift: F perpendicular to velocity, proportional to spin
        Vec3 lift_accel;
        if (ball.spin.length() > 0.01f) {
            Vec3 lift_dir = ball.spin.cross(rel_vel).normalized();
            float lift_force = 0.5f * constants.air_density *
                               constants.lift_coeff * constants.area *
                               speed * speed;
            lift_accel = lift_dir * (lift_force / constants.mass);
        }

        // Gravity
        Vec3 gravity_accel(0, -constants.gravity, 0);

        // Integrate (semi-implicit Euler)
        Vec3 total_accel = gravity_accel + drag_accel + lift_accel;
        ball.velocity = ball.velocity + total_accel * dt;
        ball.position = ball.position + ball.velocity * dt;

        // Spin decays slightly in air
        ball.spin = ball.spin * 0.999f;
    }

    /** Check if ball has hit the terrain. */
    void check_terrain_contact(BallState& ball,
                                const terrain::Terrain& terrain) {
        float ground_y = terrain.height_at_world(ball.position.x, ball.position.z);

        if (ball.position.y <= ground_y + constants.radius) {
            ball.position.y = ground_y + constants.radius;

            // Get surface properties
            auto surface_type = terrain.surface_at_world(
                ball.position.x, ball.position.z);

            // Water hazard — ball stops immediately
            if (surface_type == terrain::SurfaceType::Water) {
                ball.in_water = true;
                ball.in_flight = false;
                ball.velocity = {0, 0, 0};
                return;
            }

            auto surface = terrain::get_surface(surface_type);
            auto normal = terrain.normal_at_world(
                ball.position.x, ball.position.z);

            // Bounce
            float v_dot_n = ball.velocity.dot(normal);
            if (v_dot_n < 0) {
                // Reflect velocity off terrain normal
                ball.velocity = ball.velocity - normal * (2.0f * v_dot_n);

                // Apply restitution (energy loss)
                float restitution = surface.bounce * (1.0f - constants.bounce_loss);
                ball.velocity = ball.velocity * restitution;

                // If bounce is too weak, transition to rolling
                if (ball.velocity.y < 0.5f) {
                    ball.in_flight = false;
                    ball.rolling = true;
                    ball.velocity.y = 0;  // Cancel vertical
                }
            }
        }
    }

    /** Rolling physics: friction + slope. */
    void update_rolling(BallState& ball,
                         const terrain::Terrain& terrain, float dt) {
        float ground_y = terrain.height_at_world(
            ball.position.x, ball.position.z);
        ball.position.y = ground_y + constants.radius;

        auto surface_type = terrain.surface_at_world(
            ball.position.x, ball.position.z);

        // Water check
        if (surface_type == terrain::SurfaceType::Water) {
            ball.in_water = true;
            ball.rolling = false;
            ball.velocity = {0, 0, 0};
            return;
        }

        auto surface = terrain::get_surface(surface_type);
        auto normal = terrain.normal_at_world(
            ball.position.x, ball.position.z);

        // Slope acceleration (gravity component along terrain)
        qe::math::Vec3 gravity_vec(0, -constants.gravity, 0);
        float g_dot_n = gravity_vec.dot(normal);
        qe::math::Vec3 slope_accel = gravity_vec - normal * g_dot_n;

        // Friction deceleration
        float speed = ball.velocity.length();
        qe::math::Vec3 friction_accel;
        if (speed > 0.001f) {
            friction_accel = ball.velocity.normalized() * -1.0f *
                             surface.friction * constants.gravity;
        }

        // Speed multiplier from surface
        ball.velocity = ball.velocity + (slope_accel + friction_accel) * dt;
        ball.velocity = ball.velocity * surface.speed_mult;
        ball.position = ball.position + ball.velocity * dt;

        // Keep on terrain
        ball.position.y = terrain.height_at_world(
            ball.position.x, ball.position.z) + constants.radius;

        // Stop if slow enough
        if (ball.velocity.length() < constants.min_speed) {
            ball.velocity = {0, 0, 0};
            ball.rolling = false;
            ball.stopped = true;
        }
    }
};

} // namespace physics
} // namespace qg
