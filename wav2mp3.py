# -*- coding: utf-8 -*-
"""
WAV → MP3 Converter
- 파일/폴더 드래그앤드롭
- 기본: 원본 파일 경로에 [MP3 CONVERTED] 폴더 자동 생성 후 저장
- 옵션: 출력 경로 직접 지정
- 16/24/32bit int, 32/64bit float WAV 모두 지원 (soundfile)
- LAME 인코더 내장 (lameenc) → ffmpeg 설치 불필요
"""
import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import soundfile as sf
import lameenc

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False

OUT_DIR_NAME = "[MP3 CONVERTED]"
BITRATES = ["320", "256", "224", "192", "160", "128", "96"]
BLOCK = 262144  # frames per chunk


# ---------------------------------------------------------------- core
def collect_wavs(paths):
    """드롭된 경로들에서 .wav 파일 수집 (폴더는 하위까지 탐색)."""
    found = []
    for p in paths:
        p = os.path.normpath(p)
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d != OUT_DIR_NAME]
                for f in sorted(files):
                    if f.lower().endswith(".wav"):
                        found.append(os.path.join(root, f))
        elif os.path.isfile(p) and p.lower().endswith(".wav"):
            found.append(p)
    return found


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"


def to_int16(block, rng):
    """float32 [-1,1] → int16, TPDF 디더 적용."""
    dither = (rng.random(block.shape, dtype=np.float32)
              - rng.random(block.shape, dtype=np.float32)) / 32768.0
    x = np.clip((block + dither) * 32767.0, -32768, 32767)
    return np.round(x).astype("<i2")


def convert_file(src, dst, bitrate, progress_cb=None):
    info = sf.info(src)
    sr, ch, total = info.samplerate, info.channels, info.frames
    out_ch = 1 if ch == 1 else 2  # MP3는 최대 2채널 → 다채널은 앞 2채널(L/R) 사용

    enc = lameenc.Encoder()
    enc.set_bit_rate(int(bitrate))
    enc.set_in_sample_rate(sr)
    enc.set_channels(out_ch)
    enc.set_quality(2)  # 2 = 고품질

    rng = np.random.default_rng()
    done = 0
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    try:
        with open(tmp, "wb") as fo:
            for block in sf.blocks(src, blocksize=BLOCK, dtype="float32", always_2d=True):
                if ch > 2:
                    block = block[:, :2]
                pcm = to_int16(np.ascontiguousarray(block), rng)
                fo.write(enc.encode(pcm.tobytes()))
                done += len(block)
                if progress_cb and total:
                    progress_cb(done / total)
            fo.write(enc.flush())
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# ---------------------------------------------------------------- GUI
def _resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class App:
    def __init__(self):
        self.root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
        self.root.title("WAV → MP3 Converter")
        try:
            self.root.iconbitmap(_resource_path("icon.ico"))
        except Exception:
            pass
        self.root.geometry("720x520")
        self.root.minsize(560, 420)

        self.files = []
        self.q = queue.Queue()
        self.running = False

        self.out_mode = tk.StringVar(value="default")
        self.custom_dir = tk.StringVar(value="")
        self.bitrate = tk.StringVar(value="320")
        self.overwrite = tk.BooleanVar(value=False)
        self.open_after = tk.BooleanVar(value=True)

        self._build()
        self.root.after(100, self._poll)

    def _build(self):
        pad = {"padx": 10, "pady": 5}

        # drop zone + list
        top = ttk.LabelFrame(self.root, text=" WAV 파일 / 폴더를 여기로 드래그하세요 ")
        top.pack(fill="both", expand=True, **pad)

        cols = ("name", "status")
        self.tree = ttk.Treeview(top, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("name", text="파일")
        self.tree.heading("status", text="상태")
        self.tree.column("name", width=520)
        self.tree.column("status", width=120, anchor="center")
        sb = ttk.Scrollbar(top, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        sb.pack(side="right", fill="y", pady=6)

        if HAS_DND:
            for w in (top, self.tree):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=10)
        ttk.Button(btns, text="파일 추가…", command=self._add_files).pack(side="left")
        ttk.Button(btns, text="폴더 추가…", command=self._add_folder).pack(side="left", padx=4)
        ttk.Button(btns, text="선택 삭제", command=self._remove_sel).pack(side="left")
        ttk.Button(btns, text="목록 비우기", command=self._clear).pack(side="left", padx=4)

        # output
        out = ttk.LabelFrame(self.root, text=" 저장 위치 ")
        out.pack(fill="x", **pad)
        ttk.Radiobutton(out, text=f"원본 위치에 {OUT_DIR_NAME} 폴더 자동 생성 (기본)",
                        variable=self.out_mode, value="default",
                        command=self._toggle_custom).grid(row=0, column=0, columnspan=3, sticky="w", padx=6, pady=2)
        ttk.Radiobutton(out, text="직접 지정:", variable=self.out_mode, value="custom",
                        command=self._toggle_custom).grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.dir_entry = ttk.Entry(out, textvariable=self.custom_dir, state="disabled")
        self.dir_entry.grid(row=1, column=1, sticky="ew", padx=4)
        self.dir_btn = ttk.Button(out, text="찾아보기…", command=self._pick_dir, state="disabled")
        self.dir_btn.grid(row=1, column=2, padx=6)
        out.columnconfigure(1, weight=1)

        # options
        opt = ttk.Frame(self.root)
        opt.pack(fill="x", padx=10)
        ttk.Label(opt, text="비트레이트 (kbps, CBR):").pack(side="left")
        ttk.Combobox(opt, textvariable=self.bitrate, values=BITRATES, width=6,
                     state="readonly").pack(side="left", padx=6)
        ttk.Checkbutton(opt, text="같은 이름 덮어쓰기", variable=self.overwrite).pack(side="left", padx=12)
        ttk.Checkbutton(opt, text="완료 후 폴더 열기", variable=self.open_after).pack(side="left")

        # progress + convert
        bot = ttk.Frame(self.root)
        bot.pack(fill="x", **pad)
        self.pbar = ttk.Progressbar(bot, mode="determinate", maximum=100)
        self.pbar.pack(side="left", fill="x", expand=True)
        self.conv_btn = ttk.Button(bot, text="변환 시작", command=self._start)
        self.conv_btn.pack(side="right", padx=(8, 0))

        self.status = tk.StringVar(value="준비됨" if HAS_DND else
                                   "드래그앤드롭 불가 (tkinterdnd2 미설치) — '파일 추가' 버튼을 사용하세요")
        ttk.Label(self.root, textvariable=self.status, anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    # ---- list handling
    def _add_paths(self, paths):
        if self.running:
            return
        new = [f for f in collect_wavs(paths) if f not in self.files]
        for f in new:
            self.files.append(f)
            self.tree.insert("", "end", iid=f, values=(f, "대기"))
        self.status.set(f"{len(self.files)}개 파일" + (f"  (+{len(new)})" if new else "  — 추가된 WAV 없음"))

    def _on_drop(self, event):
        self._add_paths(self.root.tk.splitlist(event.data))

    def _add_files(self):
        self._add_paths(filedialog.askopenfilenames(filetypes=[("WAV", "*.wav *.WAV")]))

    def _add_folder(self):
        d = filedialog.askdirectory()
        if d:
            self._add_paths([d])

    def _remove_sel(self):
        if self.running:
            return
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self.files.remove(iid)
        self.status.set(f"{len(self.files)}개 파일")

    def _clear(self):
        if self.running:
            return
        self.tree.delete(*self.tree.get_children())
        self.files.clear()
        self.pbar["value"] = 0
        self.status.set("준비됨")

    def _toggle_custom(self):
        s = "normal" if self.out_mode.get() == "custom" else "disabled"
        self.dir_entry.configure(state=s)
        self.dir_btn.configure(state=s)

    def _pick_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.custom_dir.set(os.path.normpath(d))

    # ---- conversion
    def _dst_for(self, src):
        name = os.path.splitext(os.path.basename(src))[0] + ".mp3"
        if self.out_mode.get() == "custom":
            folder = self.custom_dir.get()
        else:
            folder = os.path.join(os.path.dirname(src), OUT_DIR_NAME)
        dst = os.path.join(folder, name)
        return dst if self.overwrite.get() else unique_path(dst)

    def _start(self):
        if self.running or not self.files:
            return
        if self.out_mode.get() == "custom":
            d = self.custom_dir.get().strip()
            if not d:
                messagebox.showwarning("저장 위치", "출력 폴더를 지정해 주세요.")
                return
            try:
                os.makedirs(d, exist_ok=True)
            except OSError as e:
                messagebox.showerror("저장 위치", f"폴더를 만들 수 없습니다:\n{e}")
                return
        self.running = True
        self.conv_btn.configure(state="disabled")
        for f in self.files:
            self.tree.set(f, "status", "대기")
        jobs = [(f, self._dst_for(f)) for f in self.files]
        threading.Thread(target=self._worker, args=(jobs, self.bitrate.get()), daemon=True).start()

    def _worker(self, jobs, bitrate):
        n = len(jobs)
        ok, fail, out_dirs = 0, 0, []
        for i, (src, dst) in enumerate(jobs):
            self.q.put(("row", src, "변환 중…"))
            try:
                convert_file(src, dst, bitrate,
                             lambda p, i=i: self.q.put(("prog", (i + p) / n * 100)))
                ok += 1
                d = os.path.dirname(dst)
                if d not in out_dirs:
                    out_dirs.append(d)
                self.q.put(("row", src, "완료"))
            except Exception as e:
                fail += 1
                self.q.put(("row", src, "실패"))
                self.q.put(("err", f"{os.path.basename(src)}: {e}"))
        self.q.put(("done", ok, fail, out_dirs))

    def _poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "row":
                    self.tree.set(msg[1], "status", msg[2])
                    self.tree.see(msg[1])
                elif kind == "prog":
                    self.pbar["value"] = msg[1]
                elif kind == "err":
                    self.status.set(msg[1])
                elif kind == "done":
                    _, ok, fail, dirs = msg
                    self.running = False
                    self.conv_btn.configure(state="normal")
                    self.pbar["value"] = 100
                    self.status.set(f"완료: 성공 {ok} / 실패 {fail}")
                    if self.open_after.get() and dirs:
                        for d in dirs[:3]:
                            self._open_folder(d)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    @staticmethod
    def _open_folder(path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # 명령줄 사용: python wav2mp3.py a.wav b.wav  → GUI에 목록이 채워진 채로 열림
    app = App()
    if len(sys.argv) > 1:
        app._add_paths(sys.argv[1:])
    app.run()
