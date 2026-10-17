# QA_REPORT — RigKit demo

## 1. Sprite integrity
- 52 part sprites checked, clipped at the image border: **0** 

## 2. Joint continuity (random poses within 90% of joint limits, random hands)
| rig | poses | disconnected | first failure |
|---|---|---|---|
| lulu_front | 250 | 0 | None |
| lulu_side | 250 | 0 | None |
| zaki_front | 250 | 0 | None |
| zaki_side | 250 | 0 | None |

## 3. Episode rig checks (every frame of both characters)
- frames with a joint outside its limit: **0** 
- IK ankle reach error (walk, max): **2.38e-13 units**
- planted-foot slip, side walk (max, 1130 planted foot-frames): **0.0000 px**
- planted-foot error, front standing (max): **0.0000 px**

## 4. Lip-sync vs audio envelope
| clip | corr(open, envelope) | open when loud | closed when quiet | length s |
|---|---|---|---|---|
| z1 | 0.99 | 100% | 100% | 7.47 |
| l1 | 0.97 | 100% | 100% | 7.57 |
| z2 | 0.98 | 100% | 100% | 1.97 |
| l2 | 0.99 | 100% | 100% | 1.87 |

## 5. Determinism
- two independent builds give identical pose hashes: **True** (a84df123f771)

## 6. Final video
- file: `Cartoon_RigKit_Demo.mp4` duration 00:00:33.40, frames (ffmpeg) 1002, decoded 1002, expected 1002
- minimum mean luminance of any frame: 182.8 (black frame if ≈0)
- longest run of identical consecutive frames: 0 (freeze if large)
- frame-diff spike ratio (max/median): 16.9 at frame 904

## Verdict: PASS
