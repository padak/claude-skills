#!/usr/bin/env python3
"""Recompress photos and emit data URIs for embedding.
Usage: python3 embed_photos.py <dir-with-jpgs> > photo_uris.json
Output: {"slug": "data:image/jpeg;base64,...", ...} (560px wide, q72, EXIF stripped)."""
import os, sys, json, base64, io
from PIL import Image
src=sys.argv[1]; out={}
for f in sorted(os.listdir(src)):
    if not f.lower().endswith((".jpg",".jpeg",".png")): continue
    slug=os.path.splitext(f)[0]
    im=Image.open(os.path.join(src,f)).convert("RGB")
    nw=560; nh=round(im.size[1]*nw/im.size[0])
    im=im.resize((nw,nh),Image.LANCZOS)
    buf=io.BytesIO(); im.save(buf,"JPEG",quality=72,optimize=True,progressive=True)
    out[slug]="data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()
json.dump(out,sys.stdout)
