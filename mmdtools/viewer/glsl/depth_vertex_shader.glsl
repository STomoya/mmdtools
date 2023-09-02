#version 410

layout (location = 0) in vec3 aVertex;
layout (location = 1) in vec4 aTransform0;
layout (location = 2) in vec4 aTransform1;
layout (location = 3) in vec4 aTransform2;
layout (location = 4) in vec4 aTransform3;

uniform mat4 uModelViewM;
uniform mat4 uProjectionM;

void main()
{
    mat4 Transform = mat4(aTransform0, aTransform1, aTransform2, aTransform3);
    gl_Position = uProjectionM * uModelViewM * Transform * vec4(aVertex, 1.0);
}
