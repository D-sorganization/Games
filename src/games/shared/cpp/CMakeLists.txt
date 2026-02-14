# Shared C++ Game Modules — Header-only interface libraries
#
# Usage from a game CMakeLists.txt:
#   add_subdirectory(${CMAKE_SOURCE_DIR}/src/games/shared/cpp shared_cpp)
#   target_link_libraries(my_game PRIVATE qe_math qe_core qe_input qe_renderer)
#
# Dependencies:
#   qe_math     — no deps (pure C++)
#   qe_core     — depends on qe_math
#   qe_input    — depends on SDL2
#   qe_renderer — depends on qe_core + SDL2 + OpenGL

# ── Math (no dependencies) ───────────────────────────────────────────────────
add_library(qe_math INTERFACE)
target_include_directories(qe_math INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# ── Core (depends on math) ───────────────────────────────────────────────────
add_library(qe_core INTERFACE)
target_include_directories(qe_core INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(qe_core INTERFACE qe_math)

# ── Input (depends on SDL2) ──────────────────────────────────────────────────
add_library(qe_input INTERFACE)
target_include_directories(qe_input INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
# SDL2 must be provided by the consuming project

# ── Renderer (depends on core + SDL2 + OpenGL) ──────────────────────────────
add_library(qe_renderer INTERFACE)
target_include_directories(qe_renderer INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(qe_renderer INTERFACE qe_core)
# SDL2 and OpenGL must be provided by the consuming project
