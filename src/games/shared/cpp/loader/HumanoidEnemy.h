#pragma once

#include "HumanoidRig.h"
#include "../renderer/Shader.h"
#include "../core/Transform.h"
#include "../math/Mat4.h"

#include <vector>
#include <map>
#include <memory>
#include <cmath>

namespace qe {
namespace game {

/**
 * @brief An instance of a HumanoidRig.
 * Contains only the state (joint angles, world matrices) for a single enemy.
 * References a shared HumanoidRig for mesh and hierarchy data.
 */
class HumanoidEnemy {
public:
    core::Transform transform;
    
    // Per-node state (indexed by RigNode::index)
    struct NodeState {
        float joint_angle = 0.0f;
        math::Mat4 world_matrix = math::Mat4::identity();
    };

    HumanoidEnemy() = default;

    /**
     * @brief Instantiates an enemy from a shared rig.
     */
    void set_rig(std::shared_ptr<loader::HumanoidRig> rig) {
        rig_ = rig;
        if (rig_) {
            states_.resize(rig_->nodes.size());
        }
    }

    /**
     * @brief Update animation and world matrices.
     */
    void update(float dt) {
        if (!rig_) return;

        anim_time_ += dt;
        
        // Simple animation
        set_joint("left_shoulder", std::sin(anim_time_ * 2.0f) * 0.2f);
        set_joint("right_shoulder", -std::sin(anim_time_ * 2.0f) * 0.2f);
        
        // Recalculate matrices starting from root
        if (rig_->root_index >= 0) {
            update_recursive(rig_->root_index, transform.to_matrix());
        }
    }

    void draw(renderer::Shader& shader) {
        if (!rig_) return;
        
        // Draw all nodes that have meshes
        for (const auto& node : rig_->nodes) {
            if (node.has_mesh) {
                shader.set_mat4("uModel", states_[node.index].world_matrix);
                node.mesh.draw();
            }
        }
    }
    
    void set_joint(const std::string& name, float angle) {
        if (!rig_) return;
        auto it = rig_->node_map.find(name);
        if (it != rig_->node_map.end()) {
            states_[it->second].joint_angle = angle;
        }
    }

private:
    std::shared_ptr<loader::HumanoidRig> rig_;
    std::vector<NodeState> states_;
    float anim_time_ = 0.0f;

    void update_recursive(int node_idx, const math::Mat4& parent_mat) {
        const auto& node = rig_->nodes[node_idx];
        auto& state = states_[node_idx];

        // 1. Calculate Local Transform (Bind Pose + Animation)
        math::Mat4 local_anim = math::Mat4::identity();
        
        // Only apply rotation if it's a revolute/continuous joint
        if (node.joint_type == "revolute" || node.joint_type == "continuous") {
              math::Quaternion q = math::Quaternion::from_axis_angle(
                node.joint_axis, state.joint_angle
            );
            local_anim = math::Mat4::rotate(q);
        }

        // World = Parent * BindPoseOffset * AnimRotation
        state.world_matrix = parent_mat * node.offset_matrix * local_anim;

        // 2. Recurse to children
        for (int child_idx : node.children_indices) {
            update_recursive(child_idx, state.world_matrix);
        }
    }
};

} // namespace game
} // namespace qe
