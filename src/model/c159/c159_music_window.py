"""Per-file C159 contract: NumPy selector/head and frozen Torch raw encoder.

No workspace/cache dependency, labels, fitting, network access or other-file state.
Caller supplies mono16k waveform, SAME-file PANNs intervals, frozen model/frontend/head.
"""
import numpy as np
WINDOW_SAMPLES=64000

def window_starts(num_samples):
    n=int(num_samples)
    if n<0:raise ValueError('Negative waveform length')
    if n<=WINDOW_SAMPLES:return [0]
    starts=list(range(0,n-WINDOW_SAMPLES+1,WINDOW_SAMPLES))
    if starts[-1]!=n-WINDOW_SAMPLES:starts.append(n-WINDOW_SAMPLES)
    return starts

def overlap_weighted(target_starts,target_ends,source_starts,source_ends,source_probabilities):
    # Same arithmetic and same-file nearest-interval fallback as frozen C51 C3.
    if not (len(target_starts)==len(target_ends) and len(source_starts)==len(source_ends)==len(source_probabilities) and target_starts and source_starts):
        raise ValueError('Presence interval geometry mismatch')
    if not np.isfinite(source_probabilities).all() or any(v<0 or v>1 for v in source_probabilities):
        raise ValueError('Invalid presence probability')
    result=[]
    for ts,te in zip(target_starts,target_ends):
        overlaps=[max(0,min(te,se)-max(ts,ss)) for ss,se in zip(source_starts,source_ends)]
        total=sum(overlaps)
        if total<=0:
            nearest=min(range(len(source_starts)),key=lambda j:(max(source_starts[j]-te,ts-source_ends[j],0),abs(source_starts[j]+source_ends[j]-ts-te),j))
            result.append(float(source_probabilities[nearest]))
        else:result.append(sum(o*p for o,p in zip(overlaps,source_probabilities))/total)
    return result

def select_start(num_samples,source_starts,source_ends,music_presence):
    starts=window_starts(num_samples)
    ends=[min(s+WINDOW_SAMPLES,int(num_samples)) for s in starts]
    values=overlap_weighted(starts,ends,source_starts,source_ends,music_presence)
    index=int(np.argmax(values))  # deterministic earliest-start tie break
    return starts[index],dict(starts=starts,ends=ends,music_presence=values,selected_index=index)

def extract_window(mono16k,start):
    x=np.asarray(mono16k,dtype=np.float32)
    if x.ndim!=1 or not np.isfinite(x).all():raise ValueError('Expected finite mono16k float32 vector')
    start=int(start)
    if start<0 or start>len(x):raise ValueError('Window outside audio')
    x=np.ascontiguousarray(x[start:start+WINDOW_SAMPLES],dtype=np.float32)
    if len(x)<WINDOW_SAMPLES:x=np.pad(x,(0,WINDOW_SAMPLES-len(x)),mode='constant')
    return x

def encode_raw768(model,frontend,window):
    import torch
    x=np.asarray(window,dtype=np.float32)
    if x.shape!=(WINDOW_SAMPLES,) or not np.isfinite(x).all():raise ValueError('Expected four-second input')
    inputs=frontend(x,sampling_rate=16000,return_tensors='pt')
    device=next(model.parameters()).device
    inputs={k:v.to(device) if hasattr(v,'to') else v for k,v in inputs.items()}
    with torch.inference_mode():
        output=model(**inputs)
        feature=output.hidden_states.mean(1)[0].detach().cpu().numpy().copy()
    if feature.shape!=(768,) or not np.isfinite(feature).all():raise ValueError('Invalid Dasheng raw feature')
    return feature

def predict_head(feature,head):
    x=np.asarray(feature,dtype=np.float64)
    if x.shape!=(768,):raise ValueError('Expected raw768 feature')
    z=float(((x-head['mean'])/head['scale'])@head['coef']+head['intercept'][0])
    if not np.isfinite(z):raise ValueError('Nonfinite head logit')
    if z>=0:return float(1/(1+np.exp(-z)))
    e=np.exp(z);return float(e/(1+e))

def mix_external_music(c51_music_probability,selected_probability):
    values=np.asarray([c51_music_probability,selected_probability],dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values<0) or np.any(values>1):raise ValueError('Invalid Music probability')
    return float(values.mean())
