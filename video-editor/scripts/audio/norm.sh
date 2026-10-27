# Two-pass loudnorm of audio/mix_raw.wav to -14 LUFS / -1.5 dBTP -> audio/mix.wav. Run from <film>/audio.
FF="${FFMPEG:-$(ls "$FILM_ROOT"/bin/ffmpeg* 2>/dev/null | head -1)}"; FF="${FF:-ffmpeg}"
M=$("$FF" -hide_banner -i mix_raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
II=$(echo "$M" | python -I -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
"$FF" -y -hide_banner -loglevel error -i mix_raw.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:$II:linear=true,aresample=48000" -c:a pcm_s16le mix.wav
"$FF" -hide_banner -i mix.wav -af loudnorm=I=-14:TP=-1.5:print_format=summary -f null - 2>&1 | grep -E "Input Integrated|Input True Peak"
