#!/usr/bin/env python3
"""Serve local film reviews with HTTP byte ranges for reliable media seeking."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re

class MediaHandler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def send_head(self):
        self.byte_range=None
        path=self.translate_path(self.path)
        if not os.path.isfile(path): return super().send_head()
        f=open(path,'rb')
        st=os.fstat(f.fileno()); size=st.st_size
        value=self.headers.get('Range')
        if value:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',value.strip())
            if not m or not any(m.groups()):
                f.close(); self.send_error(416,'Unsupported byte range'); return None
            a,b=m.groups()
            if a: start=int(a); end=int(b) if b else size-1
            else: start=max(0,size-int(b)); end=size-1
            if start>=size or start>end or size==0:
                f.close(); self.send_response(416); self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return None
            end=min(end,size-1); self.byte_range=(start,end);f.seek(start)
            self.send_response(206);self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            length=end-start+1
        else: self.send_response(200);length=size
        self.send_header('Content-Type',self.guess_type(path))
        self.send_header('Content-Length',str(length))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Last-Modified',self.date_time_string(st.st_mtime))
        if path.endswith(('.html','.json','.js')): self.send_header('Cache-Control','no-cache')
        self.end_headers();return f
    def copyfile(self, source, outputfile):
        try:
            if self.byte_range is None: return super().copyfile(source,outputfile)
            remaining=self.byte_range[1]-self.byte_range[0]+1
            while remaining:
                block=source.read(min(1024*1024,remaining))
                if not block:break
                outputfile.write(block);remaining-=len(block)
        except (BrokenPipeError,ConnectionResetError): pass

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=18878);args=ap.parse_args()
    root=Path(__file__).resolve().parents[2]
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(MediaHandler,directory=str(root)))
    print(f'Review server: http://127.0.0.1:{args.port}/longform/output/review.html',flush=True)
    server.serve_forever()
