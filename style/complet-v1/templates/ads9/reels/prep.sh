#!/bin/zsh
# SDR (tone-map HLG une fois) + opus pour Gemini
set -a; . ~/.claude/secrets.env; set +a
W=/Users/pro/video-editors-agents/jobs/reels-25nov/work
for n in 0352 0353 0354 0355 0356 0357 0358 0359 0360 0361 0364; do
  S=~/Downloads/IMG_$n.MOV
  ffmpeg -v error -y -i $S -map 0:a:0 -ac 1 -c:a libopus -b:a 32k $W/i$n.opus
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $S)
  (python3 /Users/pro/video-editors-agents/jobs/anti-guru-ads/work/gtr.py $W/i$n.opus $W/i${n}_g.json $D > $W/i${n}_g.txt 2>&1) &
  ffmpeg -v error -y -i $S -map 0:v:0 -map 0:a:0 -vf "zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" -c:v h264_videotoolbox -b:v 20M -c:a pcm_s16le $W/i$n.mov
  echo done $n
done
wait; echo ALL
