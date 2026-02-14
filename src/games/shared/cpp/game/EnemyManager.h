#pragma once

#include "Enemy.h"
#include <map>
#include <string>
#include <vector>
#include <iostream>
#include <cmath>

namespace qe {
namespace game {

class EnemyManager {
public:
    std::map<std::string, std::shared_ptr<loader::HumanoidRig>> rigs;
    std::vector<std::unique_ptr<Enemy>> enemies;

    void init() {
        // Load default rigs
        // Check if path exists?
        // Let's assume relative path to executable or CWD which is repo root usually
        // main.cpp used "assets/enemies/grunt/humanoid.urdf"
        auto grunt = loader::HumanoidRig::load("assets/enemies/grunt/humanoid.urdf");
        if (grunt) rigs["grunt"] = grunt;
        
        // Potential other types if they exist
        auto scout = loader::HumanoidRig::load("assets/enemies/scout/humanoid.urdf");
        if (scout) rigs["scout"] = scout;

        auto tank = loader::HumanoidRig::load("assets/enemies/tank/humanoid.urdf");
        if (tank) rigs["tank"] = tank;
    }

    void spawn(const std::string& type, const math::Vec3& pos) {
        if (rigs.find(type) == rigs.end()) {
            std::cerr << "EnemyManager: URDF for " << type << " not found!\n";
            return;
        }
        auto enemy = std::make_unique<Enemy>(rigs[type]);
        enemy->humanoid.transform.set_position(pos);
        // Default scale
        enemy->humanoid.transform.set_scale({1.0f, 1.0f, 1.0f});
        enemies.push_back(std::move(enemy));
        std::cout << "Spawned " << type << " at " << pos.x << "," << pos.z << "\n";
    }

    void update(float dt, const math::Vec3& player_pos) {
        for (auto& e : enemies) {
            // Update AI state
            e->update(dt, player_pos);
        }
    }

    void draw(renderer::Shader& shader) {
        for (auto& e : enemies) {
            e->draw(shader);
        }
    }
};

} // namespace game
} // namespace qe
