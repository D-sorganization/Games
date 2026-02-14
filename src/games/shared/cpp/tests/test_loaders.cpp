#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <filesystem>
#include <cassert>

#include "../loader/URDFLoader.h"
#include "../loader/STLLoader.h"

// Simple testing framework
#define CHECK(cond) \
    if (!(cond)) { \
        std::cerr << "FAILED: " << #cond << " at line " << __LINE__ << std::endl; \
        failed++; \
    } else { \
        passed++; \
    }

static int failed = 0;
static int passed = 0;

void test_stl_loader() {
    std::cout << "[Test] STLLoader...\n";
    // Create a dummy ASCII STL
    std::ofstream tmp("test_cube.stl");
    tmp << "solid cube\n"
        << "facet normal 0 0 -1\n"
        << "  outer loop\n"
        << "    vertex 0 1 0\n"
        << "    vertex 1 1 0\n"
        << "    vertex 1 0 0\n"
        << "  endloop\n"
        << "endfacet\n"
        << "endsolid cube\n";
    tmp.close();

    // Load it (mocking GL context by not checking GL errors)
    // Note: STLLoader calls GL functions, so this would SEGFAULT without a context if we weren't careful.
    // However, STLLoader does check if context is valid? No.
    // FIX: STLLoader is tightly coupled to OpenGL. We can't unit test it easily without a context or mocking.
    // For now, let's just verify file parsing logic if we can separating parsing from uploading.
    
    // Actually, looking at STLLoader, it DOES upload immediately.
    // Refactoring required: Split `parse` from `upload`.
}

void test_urdf_parser() {
    std::cout << "[Test] URDFLoader (Parser only)...\n";
    
    // Create dummy URDF
    std::ofstream tmp("test_robot.urdf");
    tmp << R"(
    <robot name="test_bot">
        <link name="base">
            <visual>
                <geometry><box size="1 1 1"/></geometry>
            </visual>
        </link>
        <link name="arm">
            <visual>
                <geometry><cylinder radius="0.1" length="0.5"/></geometry>
            </visual>
        </link>
        <joint name="shoulder" type="revolute">
            <parent link="base"/>
            <child link="arm"/>
            <origin xyz="0 0 1" rpy="0 0 1.57"/>
        </joint>
    </robot>
    )";
    tmp.close();

    auto result = qe::loader::URDFLoader::load("test_robot.urdf");
    
    CHECK(result.success);
    CHECK(result.model.name == "test_bot");
    CHECK(result.model.links.size() == 2);
    CHECK(result.model.joints.size() == 1);
    
    auto base_idx = result.model.link_index["base"];
    auto arm_idx = result.model.link_index["arm"];
    
    CHECK(result.model.links[base_idx].visual_geom.type == qe::loader::URDFGeomType::Box);
    CHECK(result.model.links[arm_idx].visual_geom.type == qe::loader::URDFGeomType::Cylinder);
    
    CHECK(result.model.joints[0].parent_link == "base");
    CHECK(result.model.joints[0].child_link == "arm");
    
    std::filesystem::remove("test_robot.urdf");
}

int main() {
    test_urdf_parser();
    // test_stl_loader(); // Skipped due to GL dependency
    
    std::cout << "\nResults: " << passed << " PASSED, " << failed << " FAILED.\n";
    return (failed == 0) ? 0 : 1;
}
