<p align="center"><img src="icon.png" width="128" alt="WAV2MP3 icon"></p>

<h1 align="center">WAV2MP3</h1>
<p align="center">드래그앤드롭으로 WAV 파일을 MP3로 일괄 변환하는 간단한 Windows 툴<br>
A simple drag-and-drop batch WAV → MP3 converter</p>

---

## 기능

- **드래그앤드롭**: WAV 파일이나 폴더를 창에 끌어다 놓기 (폴더는 하위 폴더까지 전부 수집)
- **기본 저장 위치**: 원본 WAV가 있는 경로에 `[MP3 CONVERTED]` 폴더를 자동 생성해 저장
- **경로 직접 지정**: 원하는 출력 폴더 선택 가능
- **비트레이트**: 96 ~ 320 kbps CBR (기본 320)
- **이름 충돌**: 기본은 `이름 (1).mp3`로 저장, 옵션으로 덮어쓰기
- 변환 완료 후 출력 폴더 자동 열기
- 16/24/32-bit int, 32-bit float WAV 지원 · 16-bit 변환 시 TPDF 디더 적용
- LAME 인코더 내장 (`lameenc`) → **ffmpeg 설치 불필요**

## 다운로드 (exe)

[Releases](../../releases) 페이지에서 `WAV2MP3.exe`를 받아 바로 실행하면 됩니다. Python 설치 필요 없음.

> 서명되지 않은 exe라 처음 실행 시 SmartScreen 경고가 뜰 수 있습니다 → **추가 정보 → 실행**

## 소스에서 실행

Python 3.9 이상 필요.

```bash
pip install -r requirements.txt
python wav2mp3.py
```

또는 Windows에서 `run.bat` 더블클릭 (첫 실행 시 패키지 자동 설치).

## exe 직접 빌드

```bash
build_exe.bat
```

`dist\WAV2MP3.exe`가 생성됩니다.

## 참고

- MP3 규격상 48kHz를 넘는 샘플레이트(88.2/96/192kHz)는 LAME가 자동으로 리샘플링합니다.
- 3채널 이상 WAV는 앞의 L/R 두 채널만 사용합니다.
- `make_icon.py`는 앱 아이콘(`icon.ico`, `icon.png`)을 생성하는 스크립트입니다 (Pillow 필요).

## License

MIT