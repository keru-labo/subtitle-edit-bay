# 編集・動画プレビュー高速化

## 現行コードと計測

| 接続箇所 | 現行の動き |
| --- | --- |
| [MainWorkflowScreen.qml](../src/ui/screens/MainWorkflowScreen.qml) | `mainWorkspacePlayer` を共有。編集位置を source 時刻に変換して seek、再生中は100msのタイマーでプロジェクト位置へ反映 |
| [WorkspacePreviewPanel.qml](../src/ui/components/WorkspacePreviewPanel.qml)・[SubtitleWorkspaceEditor.qml](../src/ui/components/SubtitleWorkspaceEditor.qml)・[SubtitleTimeline.qml](../src/ui/components/SubtitleTimeline.qml) | `VideoOutput` に表示。プレビュー、タイムライン、字幕選択が共有プレイヤーへシークを要求 |
| [AudioPreviewBridge.qml](../src/ui/components/AudioPreviewBridge.qml)・[AudioMixerPreviewSession.qml](../src/ui/components/AudioMixerPreviewSession.qml) | 音声チャンネルごとに `MediaPlayer` を用意し、選択トラックを AudioBufferOutput に渡す。プレビューのシークと再生状態を各チャンネルへ伝える |
| [gui_audio_preview_controller.py](../src/gui_audio_preview_controller.py)・[realtime_audio_mixer.py](../src/realtime_audio_mixer.py) | チャンネルのタイムスタンプ付き PCM を混合し `QAudioSink` へ出力 |
| [gui_models.py](../src/gui_models.py) | 字幕は Python の `QAbstractListModel` と範囲フィルターで提供 |

[既存 GUI ベンチマーク](GUI_PERFORMANCE.md)の 10,000 件 fixture、10ms イベントループ計測、playhead 差分、delegate 数、QML/Python 呼び出し計数を再利用する。既存の先頭フレーム計数は `QVideoSink` 通知で、シーク世代・表示時刻・音声出力位置に結びついていない。実機計測ではシーク入力、最新世代の採用、表示、音声デバイス位置を同じ単調時計で記録する。

## 試作と統合順

1. [シーク受入条件](PREVIEW_SEEK_CONTRACT.md)の制御を共通化する。Qt Multimedia を macOS・Linux と Windows の既定経路に使い、C++ の Windows アダプターは単一動画から統合する。高速経路の初期化や再生が失敗した場合は元動画・最新時刻・音量・ミュート状態を Qt 側へ引き継ぐ。
2. D3D11VA のデコードテクスチャを描画側と同一 D3D11 デバイスで扱う。コンテキストの排他、array slice、NV12/P010 の色変換、フレーム参照の寿命を管理する。別デバイスとの共有は今回の試作範囲外。GPU 内コピーを許容する経路と直接描画できる経路を分けて計測する。
3. チャンネルごとにタイムベースを変換し、ゲーム音と各話者を共通 PCM 形式へリサンプルする。トラックの開始オフセット・ゲイン・ミュートを反映し、WASAPI のオーディオクロックを映像表示の基準にする。シーク時は世代を進め、デコーダーと PCM・WASAPI キューを切り替えてから再開する。
4. プロキシは短 GOP、低解像度で生成。VFR、編集リスト、開始 PTS のずれを扱うには、元動画のプロジェクト時刻とプロキシ PTS の対応を記録し、欠落時は元動画を使う。スクラブ完了時は最新のプロジェクト時刻で元動画へ切り替える。音声はスクラブ中に止め、元動画と同じ時刻から再開する。
5. 10,000 件の操作でフレーム落ち、GUI 停止、QML/Python 呼び出しの寄与を分けて測定する。C++ へのモデル移行と Python 配布範囲は結果に基づき決める。WhisperX と書き出しは別段階で扱う。

## Windows 診断の再現

Windows で CMake 3.20 以上、C++17 ビルド環境、Qt 6 Multimedia SDK、FFmpeg の開発ライブラリを同一 ABI で用意する。CMake に Qt のインストール先を、pkg-config に FFmpeg の `.pc` ファイルを指定し、実行時には対応する DLL と Qt のプラグインをロードできるようにする。

```powershell
cmake -S src/preview -B "$env:TEMP/preview-build" -DPREVIEW_QT_PROBE=ON -DPREVIEW_D3D11_PROBE=ON
cmake --build "$env:TEMP/preview-build" --config Release
ctest --test-dir "$env:TEMP/preview-build" -C Release --output-on-failure
```

以下の実行ファイルはビルド先（マルチ構成では Release、単一構成ではビルドディレクトリ直下）から起動する。絶対パスの素材はリポジトリ外に置く。例のシーク位置は36秒以上の素材を想定している。

```powershell
$trace = 1200, 8300, 2100, 15000, 3700, 23000
.\qt_seek_probe.exe $original @trace > "$env:TEMP/qt-original.csv"
.\d3d11_decode_probe.exe $original @trace > "$env:TEMP/d3d-original.csv"
```

Qt は各シーク後の PTS 候補が `QVideoSink` に届くまで、D3D11VA は対象時刻以降のデコードテクスチャを同一デバイスの shader-resource texture へコピーする命令の発行までを記録する。D3D11VA 試作のアプリケーションコードに CPU 読み戻しはなく、テクスチャの CPU アクセス属性を検査する。コピー完了、描画、実表示、ドライバー内部転送の観測は実機で行う。Qt の時刻照合は世代の識別を保証しない。両診断は直列シークで、計測の終点が異なる。

診断用プロキシは、開始時刻がゼロで編集リストのない 60 fps CFR 素材を使う。元動画の有効範囲とテスト点は ffprobe で確認する。

```powershell
ffmpeg -i $original -map 0:v:0 -vf 'scale=-2:360' -an -c:v libx264 -pix_fmt yuv420p -g 12 -keyint_min 12 -sc_threshold 0 $proxy
.\d3d11_decode_probe.exe $proxy @trace > "$env:TEMP/d3d-proxy.csv"
```

## 実機の比較と残作業

同じ Windows PC・GPU・ドライバー・Qt/FFmpeg バージョン、同じ実況素材とトラック構成、同じ 10,000 字幕 fixture で、Qt 元動画、D3D11VA 元動画、D3D11VA プロキシの順に比較する。統合アダプターができた段階で、一定周期の入力とスクラブ終了後の再生を含む同一トレースを3回以上繰り返す。素材の元パスや名前は共有レポートに入れず、素材 ID と入力条件を記録する。

- 画面へ初めて表示された対象世代のフレームまでを測り、完了サンプルの p95 と欠落・上書き・旧世代の表示件数を併記する。表示時刻は同じ計測点で採取し、必要に応じてフレームカウンター入り素材と外部キャプチャで突き合わせる。
- 再生再開時は映像のフラッシュと各トラックのクリックを入れた素材で、最初の表示と音声出力の符号付き差分、以後のドリフトを計測する。音量・ミュート・トラックオフセットも確認する。
- `run_gui_performance.py --segment-count 10000` で既存の UI 停止と playhead 追従を採取し、同じハーネスに連続シークのシナリオを追加してから両経路を比較する。

Windows 上での両診断の実行、シーク表示 p95、WASAPI ミックスと同期、プロキシからの再生復帰、10,000 件表示中の UI 比較は未検証。
