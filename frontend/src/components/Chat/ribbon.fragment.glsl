precision mediump float; uniform float phase; uniform float dark;
    varying vec2 uv; varying vec3 normal;
    void main(){
      vec3 n=normalize(normal); if(n.z<0.)n=-n;
      float a=atan(n.x,n.z)+.16*uv.x+.2*uv.y;
      float band=.5+.5*sin(7.*a+1.25*sin(2.*a+uv.y*2.)+phase);
      float tight=exp(-55.*pow(abs(band-.71),2.));
      float rim=pow(abs(uv.x),14.);
      float v=.16+.56*smoothstep(.18,.63,band)+.26*tight+.18*rim+.045*sin(uv.x*92.)*pow(abs(uv.x),3.);
      v+=.10*dark; gl_FragColor=vec4(vec3(v*.97,v,v*1.015),1.);
    }
