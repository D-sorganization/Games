cmake_minimum_required(VERSION 3.20)

project(QuatGolf
    VERSION 0.1.0
    DESCRIPTION "3D golf game built on shared QuatEngine modules"
    LANGUAGES C CXX
)

# ── C++ Standard ──────────────────────────────────────────────────────────────
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ── Compiler Warnings ────────────────────────────────────────────────────────
if(MSVC)
    add_compile_options(/W4 /WX-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── Dependencies ─────────────────────────────────────────────────────────────
include(FetchContent)

# SDL2
FetchContent_Declare(
    SDL2
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG        release-2.30.10
    GIT_SHALLOW    TRUE
)
set(SDL_SHARED OFF CACHE BOOL "" FORCE)
set(SDL_STATIC ON  CACHE BOOL "" FORCE)
set(SDL_TEST   OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(SDL2)

find_package(OpenGL REQUIRED)

# ── Shared Engine Modules ────────────────────────────────────────────────────
# Located at Games/src/games/shared/cpp/
set(SHARED_CPP ${CMAKE_CURRENT_SOURCE_DIR}/../shared/cpp)

# ── Game Executable ──────────────────────────────────────────────────────────
add_executable(quat_golf src/main.cpp)

target_include_directories(quat_golf PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src    # Game-specific headers
    ${SHARED_CPP}                       # Shared engine headers
)

target_link_libraries(quat_golf PRIVATE
    SDL2::SDL2-static
    SDL2::SDL2main
    OpenGL::GL
)

# ── Copy Shaders ─────────────────────────────────────────────────────────────
add_custom_command(TARGET quat_golf POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_CURRENT_SOURCE_DIR}/shaders
    $<TARGET_FILE_DIR:quat_golf>/shaders
)

# ── Status ───────────────────────────────────────────────────────────────────
message(STATUS "")
message(STATUS "QuatGolf v${PROJECT_VERSION}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Shared C++:   ${SHARED_CPP}")
message(STATUS "  Build Type:   ${CMAKE_BUILD_TYPE}")
message(STATUS "")
