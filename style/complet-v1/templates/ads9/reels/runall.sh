#!/bin/zsh
cd /Users/pro/video-editors-agents/jobs/reels-25nov/work
set -a; . ~/.claude/secrets.env; set +a
for n in a13 a14 i0356 v2 v3 tof1 i0360 tof3 tof4 x99 xq xf; do
  unset LASTEND; [ $n = xf ] && export SILD=8 || unset SILD; /Users/pro/video-editors-agents/.venv/bin/python build_r.py $n > log_$n.txt 2>&1 || echo "ECHEC $n"
  python3 /Users/pro/video-editors-agents/jobs/anti-guru-ads/work/gchk.py ${n}_out.opus > gck_$n.txt 2>&1; python3 eye.py $n > /dev/null 2>&1
  echo "fini $n $(tail -1 log_$n.txt)"
done
echo TOUT
