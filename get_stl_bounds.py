import struct
with open('/mnt/e/2DPipelineScour/2DPipelineScour/constant/triSurface/Cylinder.stl', 'rb') as f:
    f.seek(80)
    n = struct.unpack('<I', f.read(4))[0]
    y_vals = []
    for _ in range(n):
        f.seek(12, 1)
        for _ in range(3):
            y_vals.append(struct.unpack('<f', f.read(4))[0])
        f.seek(2, 1)
print(min(y_vals), max(y_vals))
