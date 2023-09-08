#version 410

// VAO
layout (location = 0) in vec3 aVertex;
layout (location = 1) in vec2 aUV;
layout (location = 2) in vec3 aNormal;
layout (location = 3) in vec4 aTransform0;
layout (location = 4) in vec4 aTransform1;
layout (location = 5) in vec4 aTransform2;
layout (location = 6) in vec4 aTransform3;

// matrices
uniform mat4 uProjectionM;
uniform mat4 uModelViewM;

// variables in VAO, used in fragment shader.
out  vec2  ShareUV;
out  vec3  SharePos;
out  vec3  ShareNormal;

void main( void ) {
    mat4 Transform = mat4(aTransform0, aTransform1, aTransform2, aTransform3);
    gl_Position = uProjectionM * uModelViewM * Transform * vec4(aVertex, 1.0);
    // gl_Position = uProjectionM * uModelViewM * vec4(aVertex, 1.0);
    ShareUV = aUV;
    SharePos = aVertex;
    ShareNormal = aNormal;
}
