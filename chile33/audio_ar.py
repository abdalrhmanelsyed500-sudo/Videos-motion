import wave, numpy as np
from scipy.signal import butter, lfilter
SR=24000; DUR=12.5; n=int(DUR*SR); t=np.arange(n)/SR; r=np.random.default_rng(3); out=np.zeros(n,np.float32)
def bp(x,lo,hi): b,a=butter(2,[lo/(SR/2),hi/(SR/2)],'band'); return lfilter(b,a,x)
noise=r.normal(0,1,n).astype(np.float32)
out+=bp(noise,200,900)*(0.5+0.5*np.sin(t*0.5))*0.025            # soft wind
out+=(np.sin(2*np.pi*98*t)+0.5*np.sin(2*np.pi*147*t))*0.018*np.clip(t/2,0,1)*np.clip((DUR-t)/2,0,1)  # warm pad
for k in range(0,10):                                             # footsteps while walking
    tb=0.45+k*0.4545
    if tb<4.5:
        i=int(tb*SR); kk=np.arange(int(0.12*SR))/SR; g=0.05+0.06*(tb/4.5)
        s=(np.sin(2*np.pi*95*kk)+0.4*bp(noise[:len(kk)+10],400,1800)[:len(kk)])*np.exp(-kk*38)*g; out[i:i+len(s)]+=s
out*=np.clip((DUR-t)/1.0,0,1); out=np.tanh(out*1.2)
w=wave.open('build/mix_ar.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
