attribute vec2 param;
    uniform mediump float phase;
    varying vec2 uv;
    varying vec3 normal;
    vec3 position(vec2 p){
      float t=p.y, a=1.3+4.5*t+0.14*sin(6.0*t+phase);
      float w=(.30+.16*sin(2.5*t+1.4))*(.60+.40*cos(1.52*t));
      float s=p.x*w;
      return vec3(.36*sin(3.5*t+.4)+.22*t+s*cos(a),.86*t+s*.32*sin(3.2*t+.7),.27*sin(3.5*t)+s*sin(a)+s*s*.25);
    }
    void main(){
      uv=param; vec3 pos=position(param);
      normal=normalize(cross(position(param+vec2(.002,0.))-pos,position(param+vec2(0.,.002))-pos));
      gl_Position=vec4(pos.x+.16*pos.y,pos.y,-pos.z,1.);
    }
