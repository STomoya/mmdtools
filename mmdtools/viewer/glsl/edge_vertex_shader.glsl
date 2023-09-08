#version 410

// VAO
layout (location = 0) in vec3 aVertex;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in float aEdgeScale;
layout (location = 3) in vec4 aTransform0;
layout (location = 4) in vec4 aTransform1;
layout (location = 5) in vec4 aTransform2;
layout (location = 6) in vec4 aTransform3;

// matrices
uniform mat4 uProjectionM;
uniform mat4 uModelViewM;

// edge size
uniform float uEdgeSize;

void main() {
    mat4 Transform = mat4(aTransform0, aTransform1, aTransform2, aTransform3);
    vec4 pos = uProjectionM * uModelViewM * Transform * vec4( aVertex, 1.0 );
    vec4 pos2 = uProjectionM * uModelViewM * Transform * vec4( aVertex + aNormal, 1.0 );
    vec4 norm_d = normalize(pos2 - pos);
    gl_Position = pos + norm_d * uEdgeSize * aEdgeScale * 0.05;
}
