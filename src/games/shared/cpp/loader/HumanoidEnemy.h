#pragma once

#include "../core/Transform.h"
#include "../math/Mat4.h"
#include "../renderer/Shader.h"
#include "HumanoidRig.h"

#include <cassert>
#include <cmath>
#include <map>
#include <memory>
#include <vector>

#ifndef NDEBUG
#define QE_REQUIRE(cond, msg) assert((cond) && (msg))
#else
#define QE_REQUIRE(cond, msg) ((void)0)
#endif

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

  enum class AnimState { Idle, Walk, Panic };

  /**
   * @brief Update animation and world matrices.
   * @pre dt >= 0
   */
  void update(float dt, AnimState state = AnimState::Idle) {
    QE_REQUIRE(dt >= 0.0f, "HumanoidEnemy::update: dt must be non-negative");
    if (!rig_)
      return;

    anim_time_ += dt;

    // Reset all joints to 0 first (bind pose)
    for (auto &s : states_)
      s.joint_angle = 0.0f;

    switch (state) {
    case AnimState::Idle:
      animate_idle(anim_time_);
      break;
    case AnimState::Walk:
      animate_walk(anim_time_);
      break;
    case AnimState::Panic:
      animate_panic(anim_time_);
      break;
    }

    // Recalculate matrices starting from root
    if (rig_->root_index >= 0) {
      update_recursive(rig_->root_index, transform.to_matrix());
    }
  }

  /** Draw all mesh nodes using the given shader. */
  void draw(renderer::Shader &shader) const {
    if (!rig_)
      return;

    for (const auto &node : rig_->nodes) {
      if (node.has_mesh) {
        shader.set_mat4("uModel", states_[node.index].world_matrix);
        node.mesh.draw();
      }
    }
  }

  /** Set a named joint to a specific angle (radians). */
  void set_joint(const std::string &name, float angle) {
    if (!rig_)
      return;
    auto it = rig_->node_map.find(name);
    if (it != rig_->node_map.end()) {
      states_[it->second].joint_angle = angle;
    }
  }

  /** Check if a rig has been set. */
  bool has_rig() const noexcept { return rig_ != nullptr; }

private:
  std::shared_ptr<loader::HumanoidRig> rig_;
  std::vector<NodeState> states_;
  float anim_time_ = 0.0f;

  void animate_idle(float t) {
    float breath = std::sin(t * 1.5f);
    set_joint("spine_1", breath * 0.05f);

    float sway = std::sin(t * 1.0f + 0.5f);
    set_joint("left_shoulder", sway * 0.05f + 0.1f);
    set_joint("right_shoulder", -sway * 0.05f - 0.1f);
  }

  void animate_walk(float t) {
    float speed = 4.0f;
    float leg_swing = std::sin(t * speed);

    set_joint("left_hip", leg_swing * 0.5f);
    set_joint("right_hip", -leg_swing * 0.5f);
    set_joint("left_knee", (leg_swing > 0 ? leg_swing : 0) * 0.8f);
    set_joint("right_knee", (leg_swing < 0 ? -leg_swing : 0) * 0.8f);

    set_joint("left_shoulder", -leg_swing * 0.4f);
    set_joint("right_shoulder", leg_swing * 0.4f);
  }

  void animate_panic(float t) {
    float crazy = std::sin(t * 15.0f);
    float crazy2 = std::cos(t * 12.0f);

    set_joint("left_shoulder", crazy * 1.5f - 1.5f);
    set_joint("right_shoulder", crazy2 * 1.5f + 1.5f);
    set_joint("left_elbow", crazy2 * 1.0f);
    set_joint("right_elbow", crazy * 1.0f);
    set_joint("head", crazy * 0.2f);
  }

  void update_recursive(int node_idx, const math::Mat4 &parent_mat) {
    QE_REQUIRE(node_idx >= 0 && node_idx < static_cast<int>(rig_->nodes.size()),
               "HumanoidEnemy::update_recursive: node_idx out of bounds");

    const auto &node = rig_->nodes[node_idx];
    auto &state = states_[node_idx];

    math::Mat4 local_anim = math::Mat4::identity();

    if (node.joint_type == "revolute" || node.joint_type == "continuous") {
      math::Quaternion q =
          math::Quaternion::from_axis_angle(node.joint_axis, state.joint_angle);
      local_anim = math::Mat4::rotate(q);
    }

    state.world_matrix = parent_mat * node.offset_matrix * local_anim;

    for (int child_idx : node.children_indices) {
      update_recursive(child_idx, state.world_matrix);
    }
  }
};

} // namespace game
} // namespace qe
