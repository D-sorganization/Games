#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec3 aColor;
layout(location = 3) in vec2 aUV;

// Instanced Attributes
layout(location = 4) in mat4 aInstanceModel; // Occupies 4, 5, 6, 7
layout(location = 8) in vec3 aInstanceColor;

uniform mat4 uViewProjection;

out vec3 vWorldPos;
out vec3 vNormal;
out vec3 vColor;
out vec2 vUV;

void main() {
    mat4 model = aInstanceModel;
    vec4 worldPos = model * vec4(aPosition, 1.0);
    vWorldPos = worldPos.xyz;
    vNormal = mat3(model) * aNormal;
    vColor = aInstanceColor;
    vUV = aUV;
    gl_Position = uViewProjection * worldPos;
}
