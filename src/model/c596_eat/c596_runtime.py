"""Package-local original frozen EAT depth4/8/12 + C593 three heads + locked C594 Music fusion (C596 submission). No research paths or network loader.
Caller owns audio decoding, original C349 outputs, device choice and resource scheduling.
"""
import hashlib, importlib, json, math, sys, types
from pathlib import Path
import numpy as np

WEIGHTS=(0.43503136907024,0.26957711906879683,0.03959312199821463,0.2557983898627485)
ORDER=('D239','Fourier','Dasheng','C593_EAT_multiwindow')
FUSION_SOURCE_SHA256='47ee3051a72cc1a97cdecbb2f1a360d9825ff8c0be0d057ff94c6325dd3c1822'
TRAINING_UPDATES=1650
TRAINING_ROWS=4400
TRAINING_EPOCHS=6
ASSETS={
 'config.json':(779,'2e7d67b4c77586cd495c9691152e49280c6be720a0e04da2c66822b1e94503ff'),
 'configuration_eat.py':(1768,'761f19555f0d53aa7725ffb83a6e4eec652af97244134ea5147edca71be9b9e5'),
 'eat_model.py':(3670,'9a836c65a7e02e7b3df80cca93324ff96d50b3c380a777c393803671e17faf37'),
 'model_core.py':(6928,'f0157ab1d7f59e07db6da9d7845099dac7b818e1ea69322936da83364d8a2768'),
 'modeling_eat.py':(467,'41eaf4b87923a56ef13899cbbe6d6ec9642d1f58db2e0b2661aae611eccfce9f'),
 'model.safetensors':(359905840,'8623072d09aac4f3ad1168b4fed3a24e4f68fe1da25b9fe733375efb237e5f48'),
 'C593_FINAL_MODEL.pt':(1832109,'3b788240581c7fe6e53859f6009c63f92139a62db670e8f85466a930ccf375fa')}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()

def logit(p):
    p=min(1-1e-6,max(1e-6,float(p)));return math.log(p/(1-p))

def fbank(raw):
    import torch,torchaudio
    assert raw.shape==(64000,) and raw.dtype==np.float32 and np.isfinite(raw).all()
    wave=torch.from_numpy(raw.copy());wave=wave-wave.mean()
    mel=torchaudio.compliance.kaldi.fbank(wave.unsqueeze(0),htk_compat=True,sample_frequency=16000,
        use_energy=False,window_type='hanning',num_mel_bins=128,dither=0.,frame_shift=10)
    frames=int(mel.shape[0]);mel=torch.nn.functional.pad(mel,(0,0,0,max(0,400-frames)))[:400]
    x=((mel+4.268)/(4.569*2)).unsqueeze(0).unsqueeze(0)
    assert x.shape==(1,1,400,128) and torch.isfinite(x).all();return x,frames

class C596Music:
    def __init__(self,asset_dir,device='cpu'):
        import torch,timm
        from safetensors.torch import load_file
        assert timm.__version__=='0.9.12'
        self.device=torch.device(device);assert self.device.type in ('cpu','cuda')
        base=Path(asset_dir).resolve();paths={}
        for name,(size,digest) in ASSETS.items():
            path=(base/name).resolve();assert path.is_relative_to(base)
            assert path.stat().st_size==size and sha(path)==digest,name;paths[name]=path
        package_name='_c596_original_eat_'+hashlib.sha256(str(base).encode()).hexdigest()[:12]
        package=types.ModuleType(package_name);package.__path__=[str(base)];package.__package__=package_name
        sys.modules[package_name]=package
        config_class=importlib.import_module(package_name+'.configuration_eat').EATConfig
        model_class=importlib.import_module(package_name+'.modeling_eat').EATModel
        config=config_class(**json.loads(paths['config.json'].read_text(encoding='utf-8')))
        assert config.model_variant=='pretrain' and config.embed_dim==768 and config.depth==12 and config.layer_norm_first is False
        with torch.random.fork_rng(devices=[]),torch.device('cpu'):
            self.model=model_class(config).cpu().eval().requires_grad_(False)
            self.heads=torch.nn.ModuleList([torch.nn.Sequential(torch.nn.LayerNorm(2304),torch.nn.Linear(2304,64),torch.nn.GELU(),torch.nn.Linear(64,1)) for _ in range(3)]).cpu().eval().requires_grad_(False)
        state=load_file(str(paths['model.safetensors']),device='cpu');expected=self.model.state_dict()
        assert set(state)==set(expected) and len(state)==150 and sum(v.numel() for v in state.values())==89972736
        for name,value in state.items():
            assert value.shape==expected[name].shape and value.dtype==expected[name].dtype and torch.isfinite(value).all(),name
        self.model.load_state_dict(state,strict=True)
        assert all(torch.equal(v,self.model.state_dict()[k]) for k,v in state.items())
        del state,expected
        learned=torch.load(paths['C593_FINAL_MODEL.pt'],map_location='cpu',weights_only=True);assert set(learned)=={'heads'}
        current=self.heads.state_dict();assert set(learned['heads'])==set(current)
        for key,value in learned['heads'].items():
            assert value.shape==current[key].shape and value.dtype==current[key].dtype and torch.isfinite(value).all(),key
        self.heads.load_state_dict(learned['heads'],strict=True)
        assert sum(p.numel() for p in self.heads.parameters())==456579
        assert all(torch.equal(v,self.heads.state_dict()[k]) for k,v in learned['heads'].items())
        del learned,current
        self.model.to(self.device);self.heads.to(self.device)
        assert len(WEIGHTS)==4 and min(WEIGHTS)>=0 and abs(sum(WEIGHTS)-1)<=1e-12

    def features(self,raw):
        import torch
        x,_=fbank(raw);captured={};handles=[]
        assert not self.model.training and all(not p.requires_grad for p in self.model.parameters())
        def pool(tokens):
            assert tokens.shape==(1,201,768) and torch.isfinite(tokens).all()
            patch=tokens[:,1:];return torch.cat((tokens[:,0],patch.mean(1),patch.std(1,unbiased=False)),dim=1)
        def capture(index):
            def hook(_module,_inputs,output):
                assert isinstance(output,tuple) and len(output)==2 and index not in captured
                captured[index]=pool(output[0]).detach()
            return hook
        try:
            for index in (3,7,11):handles.append(self.model.model.blocks[index].register_forward_hook(capture(index)))
            with torch.inference_mode():
                final=self.model.extract_features(x.to(self.device))
                assert set(captured)=={3,7,11} and torch.equal(captured[11],pool(final))
                feature=torch.stack([captured[index] for index in (3,7,11)],dim=1)
        finally:
            for handle in handles:handle.remove()
        assert feature.shape==(1,3,2304) and torch.isfinite(feature).all();return feature

    def per_head_logits(self,features):
        import torch
        assert features.shape==(1,3,2304)
        return torch.stack([self.heads[i](features[:,i]).reshape(-1) for i in range(3)],dim=1)

    def window_probability(self,raw):
        import torch
        with torch.inference_mode():p=float(self.per_head_logits(self.features(raw)).mean(dim=1).sigmoid()[0].item())
        assert math.isfinite(p) and 0<=p<=1;return p

    def predict(self,raw,anchor,presence_starts,presence_ends,music_presence_segments,D239,Fourier,Dasheng):
        """One decoded mono float32/16k file; all intervals refer to this same raw waveform."""
        assert raw.ndim==1 and len(raw)>0 and raw.dtype==np.float32 and np.isfinite(raw).all()
        assert len(presence_starts)==len(presence_ends)==len(music_presence_segments)>0
        assert all(0<=s<e for s,e in zip(presence_starts,presence_ends))
        assert all(math.isfinite(p) and 0<=p<=1 for p in music_presence_segments)
        starts=anchor.get_segment_starts(len(raw),64000,6);ends=[min(s+64000,len(raw)) for s in starts]
        weights=np.asarray(anchor.c3_overlap_weighted(starts,ends,presence_starts,presence_ends,music_presence_segments),dtype=np.float64)
        assert weights.shape==(len(starts),) and np.isfinite(weights).all() and np.all((weights>=0)&(weights<=1))
        values=[]
        for start,end in zip(starts,ends):
            wave=np.zeros(64000,np.float32);wave[:end-start]=raw[start:end];values.append(self.window_probability(wave))
        mean=float(np.mean(values,dtype=np.float64));total=weights.sum()
        raw_pool=float(values[0]) if len(values)==1 else (mean if total==0 else float(np.dot(np.asarray(values,np.float64),weights)/total))
        assert math.isfinite(raw_pool) and -1e-12<=raw_pool<=1+1e-12
        standalone=min(1.,max(0.,raw_pool));assert logit(standalone)==logit(raw_pool)
        assert all(math.isfinite(p) and -1e-12<=p<=1+1e-12 for p in (D239,Fourier,Dasheng))
        z=sum(w*logit(p) for w,p in zip(WEIGHTS,(D239,Fourier,Dasheng,raw_pool)))
        fused=1/(1+math.exp(-z));assert math.isfinite(fused) and 0<=fused<=1
        return dict(EAT_multiwindow=standalone,EAT_raw_pooled=raw_pool,Music=fused,starts=starts,ends=ends,
                    window_probabilities=values,presence_weights=weights.tolist())
