#pragma once

#include "../loader/HumanoidEnemy.h"
#include "../renderer/Shader.h"
#include "../math/Vec3.h"

namespace qe {
namespace game {

enum class EnemyState {
    Idle,
    Watch,
    Panic, // Goalkeeper logic or run away
    Celebrate
};

class Enemy {
public:
    EnemyState state = EnemyState::Idle;
    loader::HumanoidEnemy humanoid;
    math::Vec3 velocity = {0,0,0};
    float speed = 2.0f;
    float state_timer = 0.0f;

    Enemy(std::shared_ptr<loader::HumanoidRig> rig) {
        humanoid.set_rig(rig);
    }

    void update(float dt, const math::Vec3& player_pos) {
        state_timer += dt;
        
        loader::HumanoidEnemy::AnimState anim = loader::HumanoidEnemy::AnimState::Idle;
        
        // Simple state machine
        switch(state) {
            case EnemyState::Idle:
                anim = loader::HumanoidEnemy::AnimState::Idle;
                if (state_timer > 3.0f) {
                    state = EnemyState::Watch;
                    state_timer = 0;
                }
                break;
            case EnemyState::Watch: {
                anim = loader::HumanoidEnemy::AnimState::Idle; // Or Walk if moving?
                // Look at player/ball
                auto dir = (player_pos - humanoid.transform.position()).normalized();
                float target_yaw = std::atan2(dir.x, -dir.z); 
                // Smooth turn
                // For now, snap
                humanoid.transform.set_rotation(
                    math::Quaternion::from_euler(0, target_yaw + 3.14159f, 0)
                );
                
                if (state_timer > 5.0f) {
                    state = EnemyState::Idle;
                    state_timer = 0;
                }
                break;
            }
            case EnemyState::Panic:
                anim = loader::HumanoidEnemy::AnimState::Panic;
                break;
            case EnemyState::Celebrate:
                anim = loader::HumanoidEnemy::AnimState::Panic; // Celebrate looks like Panic for now
                break;
        }

        humanoid.update(dt, anim);
    }

    void draw(renderer::Shader& shader) {
        humanoid.draw(shader);
    }

    bool check_collision(const math::Vec3& sphere_pos, float sphere_radius, math::Vec3& out_normal, float& out_depth) {
        // Simple Cylinder vs Sphere
        float cy_r = 0.4f;
        float cy_h = 1.8f;
        math::Vec3 pos = humanoid.transform.position();

        // 1. Check Y range (vertical overlap)
        if (sphere_pos.y + sphere_radius < pos.y || sphere_pos.y - sphere_radius > pos.y + cy_h) {
            return false;
        }

        // 2. Check XZ distance (horizontal overlap)
        float dx = sphere_pos.x - pos.x;
        float dz = sphere_pos.z - pos.z;
        float dist_sq = dx*dx + dz*dz;
        float combined_r = cy_r + sphere_radius;

        if (dist_sq > combined_r * combined_r) {
            return false;
        }

        // Collision detected
        // Calculate normal in XZ plane
        if (dist_sq < 0.0001f) {
            out_normal = {1, 0, 0}; // Degenerate case
        } else {
            out_normal = math::Vec3(dx, 0, dz).normalized();
        }
        out_depth = combined_r - std::sqrt(dist_sq);
        return true;
    }
};

} // namespace game
} // namespace qe
