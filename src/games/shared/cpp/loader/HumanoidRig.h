#pragma once

#include "../math/Mat4.h"
#include "../math/Quaternion.h"
#include "../renderer/Mesh.h"
#include "STLLoader.h"
#include "URDFLoader.h"

#include <map>
#include <memory>
#include <string>
#include <vector>

namespace qe {
namespace loader {

/**
 * @brief A node in the static rig hierarchy.
 * Contains bind pose information and visual mesh data.
 */
struct RigNode {
  std::string name;
  int index = -1; // Linear index in rig array

  // Visuals
  renderer::Mesh mesh;
  bool has_mesh = false;

  // Bind Pose (Parent -> Child)
  math::Mat4 offset_matrix = math::Mat4::identity();

  // Joint Definition
  std::string joint_type; // "revolute", "fixed"
  math::Vec3 joint_axis{0, 0, 1};

  // Hierarchy
  int parent_index = -1;
  std::vector<int> children_indices;
};

/**
 * @brief Represents the shared, read-only data for a humanoid model.
 * Load this ONCE per enemy type (e.g. once for "Grunt", once for "Scout").
 */
class HumanoidRig {
public:
  std::string name;
  std::vector<RigNode> nodes;
  std::map<std::string, int> node_map;
  std::vector<std::string> warnings;
  int root_index = -1;

  /**
   * @brief Load rig from URDF file.
   * @return nullptr on failure.
   */
  static std::shared_ptr<HumanoidRig> load(const std::string &urdf_path) {
    auto result = URDFLoader::load(urdf_path);
    if (!result.success) {
      // Loader should return error in result
      return nullptr;
    }

    auto rig = std::make_shared<HumanoidRig>();
    rig->name = result.model.name;

    // 1. Create linear list of nodes based on URDF links
    // We use the URDF link index as our rig index for simplicity
    rig->nodes.resize(result.model.links.size());

    for (const auto &kv : result.model.link_index) {
      int idx = kv.second;
      rig->nodes[idx].name = kv.first;
      rig->nodes[idx].index = idx;
      rig->node_map[kv.first] = idx;

      // Load Mesh
      const auto &link = result.model.links[idx];
      if (link.visual_geom.type == URDFGeomType::Mesh &&
          !link.visual_geom.mesh_filename.empty()) {

        // base_dir already ends with '/' — avoid double-slash
        std::string full_path =
            result.base_dir + link.visual_geom.mesh_filename;
        auto stl = STLLoader::load(full_path, link.color.r, link.color.g,
                                   link.color.b);

        if (stl.success) {
          rig->nodes[idx].mesh = std::move(stl.mesh);
          rig->nodes[idx].has_mesh = true;
        } else {
          rig->warnings.push_back("Failed to load mesh: " + full_path + " (" +
                                  stl.error + ")");
        }
      }
    }

    // 2. Build Hierarchy from Joints
    for (const auto &joint : result.model.joints) {
      if (rig->node_map.count(joint.parent_link) &&
          rig->node_map.count(joint.child_link)) {
        int p_idx = rig->node_map[joint.parent_link];
        int c_idx = rig->node_map[joint.child_link];

        rig->nodes[c_idx].parent_index = p_idx;
        rig->nodes[p_idx].children_indices.push_back(c_idx);

        // Calc Bind Pose Offset
        math::Quaternion rot = math::Quaternion::from_euler(
            joint.origin.rpy.x, joint.origin.rpy.y, joint.origin.rpy.z);
        math::Mat4 trans = math::Mat4::translate(joint.origin.xyz);

        rig->nodes[c_idx].offset_matrix = trans * math::Mat4::rotate(rot);
        rig->nodes[c_idx].joint_axis = joint.axis;
        rig->nodes[c_idx].joint_type = joint.type;
      }
    }

    // 3. Find Root
    std::string root_name = result.model.root_link_name();
    if (rig->node_map.count(root_name)) {
      rig->root_index = rig->node_map[root_name];
    }

    return rig;
  }

  // RAII: Meshes are destroyed when the last referencing Rig is destroyed
  ~HumanoidRig() {
    for (auto &node : nodes) {
      if (node.has_mesh)
        node.mesh.destroy();
    }
  }
};

} // namespace loader
} // namespace qe
