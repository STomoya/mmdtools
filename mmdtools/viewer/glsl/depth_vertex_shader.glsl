#version 410

layout (location = 0) in vec3 aVertex;

uniform mat4 uModelViewM;
uniform mat4 uProjectionM;

void main()
{
    gl_Position = uProjectionM * uModelViewM * vec4(aVertex, 1.0);
}
