# ドキュメント索引（全件カタログ）

本ディレクトリ（`docs/`）配下の全 Markdown ドキュメント（全 **56 件**）を 5 つのカテゴリに分類した全体索引です。
主要な入口はリポジトリトップの [README.md](../README.md) にも掲載しています。

## カテゴリ一覧

| カテゴリ | 件数 | 想定読者 | 役割・位置づけ |
| --- | ---: | --- | --- |
| [1. 利用ガイド (`User Guide`)](#1-利用ガイド-user-guide) | 8 件 | 利用者（一部開発者） | 導入、画面操作、CLI 実行、設定、トラブル解決の手順書 |
| [2. 設計・仕様 (`Architecture & Design`)](#2-設計仕様-architecture--design) | 23 件 | 開発者 | GUI 構造、ワークスペース境界、データモデル、AI Action 境界、音声・字幕パイプライン仕様 |
| [3. 運用・リリース (`Release & Runtime`)](#3-運用リリース-release--runtime) | 5 件 | 開発者 | リリース手順、候補昇格、Windows ランタイム契約、バイナリ署名、インストーラー移行 |
| [4. 品質・テスト (`Quality & CI`)](#4-品質テスト-quality--ci) | 6 件 | 開発者 | CI テストグループ、PR 検証責務、Ruff/mypy 品質ゲート、GUI 性能、実音声 ASR 評価 |
| [5. 作業記録・履歴 (`Archive / Historical`)](#5-作業記録履歴-archive--historical) | 14 件 | 開発者（履歴参照） | 完了済み Epic の計画・ロードマップ、段階導入時の中間メモ、監査記録、試行ログ |

---

## 1. 利用ガイド (`User Guide`)

導入・日々の編集操作・設定調整・トラブル切り分けを行う利用者向けのガイド群です。

| ドキュメント | 想定読者 | 概要（1行） | 正本コード / 関連領域 | 状態 |
| --- | --- | --- | --- | --- |
| [USAGE.md](USAGE.md) | 利用者（一部開発者） | セットアップ、GUI 操作、CLI 各パイプライン、ショートモードの総合利用ガイド | `src/gui.py`, `src/subtitle_workflow.py`, `src/craig_pipeline.py`, `src/batch.py`, `src/pipeline.py`, `src/silence_cut.py`, `src/burn_subs.py`, `src/short_video.py` | Active |
| [CONFIGURATION.md](CONFIGURATION.md) | 利用者 / 開発者 | 実行設定（GPU・字幕・音声分離・codec）、編集プロジェクト、話者色設定の項目と優先順位 | `src/runtime_config.py`, `src/runtime_config_schema.py`, `src/runtime_settings.py`, `src/color_config.py`, `src/subtitle_project_schema.py`, `assets/runtime_config.json` | Active |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 利用者（一部開発者） | セットアップ、GUI、FFmpeg/WhisperX/CUDA、無音カット、ミキサー、Codex、ショートのトラブル対処手順 | `setup.bat`, `update.bat`, `src/craig_pipeline.py`, `src/gui.py`, `src/audio_preview_cache.py`, `src/codex_ai_provider.py`, `src/short_video.py` | Active |
| [NON_DESTRUCTIVE_CUTS.md](NON_DESTRUCTIVE_CUTS.md) | 利用者 / 開発者 | 通常動画の非破壊カット機能の GUI 操作手順、JSON 保存形式、素材時間と出力時間の計算・書き出し規則 | `src/video_timeline.py`, `src/editor_workspace.py`, `src/silence_cut.py`, `src/burn_subs.py`, `src/ui/components/CutModeTimeline.qml`, `src/ui/components/CutModeSettings.qml` | Active |
| [PROCESS_PROGRESS.md](PROCESS_PROGRESS.md) | 利用者 / 開発者 | 画面下部の処理進捗パネルの記号、全体進捗、システムログ、`PROGRESS_EVENT` の見方 | `src/processing_progress.py`, `src/application_logging.py`, `src/gui_workflow_facade.py`, `src/ui/components/ProcessingProgressPanel.qml`, `src/ui/components/ApplicationLogPanel.qml` | Active |
| [SUBTITLE_LINE_COUNT.md](SUBTITLE_LINE_COUNT.md) | 利用者 / 開発者 | 字幕の自動改行・`Enter` による手動改行の操作方法、旧行数設定からの移行、ページ分割の時刻配分規則 | `src/subtitle_line_count.py`, `src/subtitle_line_count_config.py`, `src/subtitle_packer.py`, `src/subtitle_layout/` | Active |
| [CODEX_CHAT.md](CODEX_CHAT.md) | 利用者 / 開発者 | Codex チャットのログイン、モデル選択、字幕編集提案の操作手順と `AIProvider` セキュリティ境界 | `src/ai_provider.py`, `src/codex_ai_provider.py`, `src/gemini_acp_provider.py`, `src/gui_ai_chat_state.py`, `src/gui_codex_chat_state.py`, `src/gui_ai_facade.py`, `src/ui/components/CodexChatPanel.qml` | Active |
| [CODEX_EDITING.md](CODEX_EDITING.md) | 利用者 / 開発者 | Codex を使った字幕編集提案の導入、対象範囲 5 種の選択、データ保護、診断手順 | `src/codex_edit_proposal.py`, `src/gui_codex_state.py`, `src/gui_ai_facade.py`, `src/ui/components/CodexEditPanel.qml`, `src/ui/components/CodexChatPanel.qml` | Active |

---

## 2. 設計・仕様 (`Architecture & Design`)

GUI アーキテクチャ、ワークスペース状態、音声・文字起こし・字幕・動画合成パイプライン、AI Action 境界の設計仕様書群です。

| ドキュメント | 想定読者 | 概要（1行） | 正本コード / 関連領域 | 状態 |
| --- | --- | --- | --- | --- |
| [GUI_ARCHITECTURE.md](GUI_ARCHITECTURE.md) | 開発者 | Python GUI state 分割、QML コンポーネント境界、`ProjectEditorController` による編集確定境界の設計 | `src/gui.py`, `src/gui_state_base.py`, `src/gui_source_state.py`, `src/gui_runtime_state.py`, `src/gui_project_editor_controller.py`, `src/ui/Main.qml`, `src/ui/screens/MainWorkflowScreen.qml`, `src/ui/components/*.qml` | Active |
| [GUI_FEATURES.md](GUI_FEATURES.md) | 開発者 | QML へ公開する 8 つの機能別 Facade（`subtitles`, `audio`, `ai`, `workflow`, `workspace`, `sequence`, `shortVideo`, `updates`）の責務と互換層 | `src/gui_feature_facade.py`, `src/gui_subtitles_facade.py`, `src/gui_audio_facade.py`, `src/gui_ai_facade.py`, `src/gui_workflow_facade.py`, `src/gui_workspace_facade.py`, `src/gui_sequence_facade.py`, `src/gui_short_video_facade.py`, `src/gui_updates_facade.py`, `src/gui_backend_compatibility.py` | Active |
| [EDITOR_WORKSPACE.md](EDITOR_WORKSPACE.md) | 開発者 | 通常動画編集ワークスペースにおける `currentEditMode`（`subtitle`/`cut`/`audio`）と `editorPlayhead` の状態契約 | `src/editor_workspace.py`, `src/gui_workspace_controller.py`, `src/gui_workspace_facade.py`, `src/ui/screens/MainWorkflowScreen.qml` | Active |
| [workspace-actions.md](workspace-actions.md) | 開発者 / 利用者 | プロジェクト開始画面、`actionCapabilities` の有効条件表、プロジェクト保存先・完成動画出力先・作業フォルダの分離仕様 | `src/workflow_actions.py`, `src/gui_workflow_facade.py`, `src/subtitle_workflow.py`, `src/ui/components/ProjectStartScreen.qml`, `src/ui/components/ProjectStartFlow.qml` | Active |
| [SHORT_WORKSPACE.md](SHORT_WORKSPACE.md) | 開発者 | ショート用ワークスペース（`short-artifact`）の状態境界、時刻基準（`time_basis=source`）、完成尺計算、本編選択範囲からの bridge 契約 | `src/short_video_timeline.py`, `src/short_video.py`, `src/short_video_schema.py`, `src/gui_workspace_controller.py`, `src/gui_short_video_facade.py`, `src/ui/screens/ShortModeScreen.qml`, `docs/short-workspace-contract.js` | Active |
| [MULTI_SOURCE_SHORT_VIDEO.md](MULTI_SOURCE_SHORT_VIDEO.md) | 開発者 | 複数素材の `source_id` 管理、再リンク、時刻正規化、ショート動画フィルタ生成の境界仕様 | `src/multi_source_short_video.py`, `src/video_sequence.py` | Active |
| [video-assembly-design.md](video-assembly-design.md) | 開発者 | 動画連結・シーケンス結合モードの UI レイアウト、データモデル、複数素材×音声の紐づけ、FFmpeg 連携設計 | `src/assemble_video.py`, `src/video_sequence.py`, `src/sequence_render.py`, `src/multi_source_short_video.py`, `src/ui/components/SequenceEditorPanel.qml`, `src/ui/components/MediaBinPanel.qml`, `docs/ui-redesign-mockup.html` | Active |
| [HIGHLIGHT_DETECTION.md](HIGHLIGHT_DETECTION.md) | 開発者 | 見どころ候補検出のデータ境界、候補選定制約、フィードバック学習と効果測定契約 | `src/highlight_candidates.py`, `src/highlight_signals.py`, `src/highlight_visual_signals.py`, `src/highlight_feedback.py`, `src/highlight_preferences.py`, `src/codex_highlight_ranker.py`, `src/gui_short_video_facade.py`, `src/ui/components/HighlightCandidateList.qml` | Active |
| [CODEX_ACTIONS.md](CODEX_ACTIONS.md) | 開発者 | AI Action ディスパッチの型・スコープ・対象 revision 検証境界とスキーマ契約 | `src/codex_actions.py`, `schemas/codex_action.schema.json`, `src/gui_ai_facade.py` | Active |
| [CODEX_AUDIO_MIX.md](CODEX_AUDIO_MIX.md) | 開発者 | `propose_audio_mix` Action と音量ミックス提案スキーマのデータ契約・検証フロー | `src/audio_mix_proposal.py`, `src/audio_mixer.py`, `src/codex_actions.py`, `schemas/codex_audio_mix_proposal.schema.json`, `src/gui_audio_facade.py` | Active |
| [TRANSCRIPTION_ACCURACY.md](TRANSCRIPTION_ACCURACY.md) | 開発者 | 初回文字起こしの生成パラメータ（`beam_size=10`, `repetition_penalty=1.1`, `chunk_size=15`, VAD 閾値）の設計根拠と WhisperX 3.8.6 実効性 | `src/transcription_profile.py`, `src/whisperx_runner.py`, `src/transcribe.py`, `src/transcription_execution.py` | Active |
| [TRANSCRIPTION_DICTIONARY.md](TRANSCRIPTION_DICTIONARY.md) | 利用者 / 開発者 | ゲーム固有名詞辞書の GUI / CLI ワークフロー、手動辞書 JSON 形式、確認済み辞書のキャッシュ挙動 | `src/transcription_dictionary.py`, `src/transcription_context.py`, `src/transcription_web_dictionary.py`, `src/transcription_dictionary_suggestions.py`, `src/gui_transcription_context_state.py`, `src/ui/components/TranscriptionContextPanel.qml` | Active |
| [TRANSCRIPTION_EXECUTION.md](TRANSCRIPTION_EXECUTION.md) | 開発者 | 単一音声文字起こし実行（`transcribe_audio_with_cache()`）とキャッシュ検証・`skip_existing` の境界 | `src/transcription_execution.py`, `src/transcribe.py`, `src/whisperx_runner.py` | Active |
| [CRAIG_TRANSCRIPTION_EXECUTION.md](CRAIG_TRANSCRIPTION_EXECUTION.md) | 開発者 | Craig 複数話者音声の文字起こし実行境界とヒント解決順序の定義 | `src/craig_transcription_execution.py` | Active |
| [TRANSCRIPT_CACHE.md](TRANSCRIPT_CACHE.md) | 開発者 | 文字起こしキャッシュ fingerprint の入力項目、`.cache.json` sidecar 形式、有効性判定関数の仕様 | `src/transcript_cache.py`, `src/transcription_execution.py` | Active |
| [RUNTIME_SETTINGS.md](RUNTIME_SETTINGS.md) | 開発者 | `runtime_settings.py` の型付き設定グループとアダプター関数の設計・移行方針 | `src/runtime_settings.py`, `src/runtime_config.py`, `src/subtitle_workflow.py`, `src/gui_runtime_state.py` | Active |
| [subtitle-domain-models.md](subtitle-domain-models.md) | 開発者 | 字幕プロジェクトのドメインモデル（`SubtitleSegment`, `SpeakerInfo`, `WaveformInfo`, `AudioMix`, `SubtitleProject`）と変換経路 | `src/subtitle_project.py`, `src/subtitle_project_schema.py`, `src/subtitle_project_model.py` | Active |
| [pipeline_stages.md](pipeline_stages.md) | 開発者 | `craig_pipeline.py` と `subtitle_workflow.py` におけるステージ分割ヘルパー関数と戻り値型の設計 | `src/craig_pipeline.py`, `src/subtitle_workflow.py`, `src/subtitle_workflow_transcription.py` | Active |
| [EXPORT_FORMATS.md](EXPORT_FORMATS.md) | 開発者 / 利用者 | SRT / WebVTT / CSV 字幕書き出しおよびタイムライン JSON / CMX 3600 EDL 出力の仕様と安全性要件 | `src/subtitle_export.py`, `src/timeline_interchange.py` | Active |
| [PROJECT_RECOVERY.md](PROJECT_RECOVERY.md) | 開発者 | プロジェクトのスナップショット保存形式、SHA-256 整合性検証、クラッシュ復旧 journal の仕様 | `src/project_snapshots.py`, `src/project_recovery.py` | Active |
| [YOUTUBE_POST_PACKAGE.md](YOUTUBE_POST_PACKAGE.md) | 開発者 / 利用者 | YouTube 投稿用ローカルパッケージ出力とサムネイル候補・チャプター検証の仕様 | `src/youtube_package.py`, `src/youtube_text.py`, `src/thumbnail_candidates.py` | Active |
| [PLATFORM_BOUNDARIES.md](PLATFORM_BOUNDARIES.md) | 開発者 | Windows / POSIX 間のプロセス起動・停止、保存先パス、自動更新の OS 差分境界モジュール設計 | `src/process_utils.py`, `src/qprocess_launcher.py`, `src/platform_paths.py`, `src/platform_updates.py`, `src/gui_job_runner.py` | Active |
| [GUI_UPDATES.md](GUI_UPDATES.md) | 開発者 | Installer 版の GUI 更新確認・ダウンロード・検証・終了後適用・ロールバックの状態遷移と契約 | `src/update_manager.py`, `src/updater.py`, `src/platform_updates.py`, `src/gui_updates_facade.py`, `scripts/apply_installer_update.ps1`, `scripts/update.ps1` | Active |

---

## 3. 運用・リリース (`Release & Runtime`)

リリース公開手順、候補成果物の昇格、Windows ランタイム世代管理、ネイティブバイナリ署名、ZIP 版から Installer 版への移行手順を扱う文書群です。

| ドキュメント | 想定読者 | 概要（1行） | 正本コード / 関連領域 | 状態 |
| --- | --- | --- | --- | --- |
| [RELEASING.md](RELEASING.md) | 開発者 | `VERSION` PR によるリリース手順、マージ前 `Release readiness`、マージ後の候補昇格公開、必須チェックと公開後確認 | `.github/workflows/release-readiness.yml`, `.github/workflows/release-prepare.yml`, `.github/workflows/release-request.yml`, `.github/workflows/release.yml`, `scripts/release_readiness.py`, `scripts/release_candidate.py`, `scripts/release_contract.py`, `scripts/release_state.py` | Active |
| [release-candidate-promotion.md](release-candidate-promotion.md) | 開発者 | マージ前 `Release readiness` 成果物の検証・昇格条件と再実行・復旧契約の詳細仕様 | `scripts/release_candidate.py`, `scripts/release_contract.py`, `scripts/release_state.py`, `.github/workflows/release.yml`, `.github/workflows/release-request.yml` | Active |
| [RUNTIME_CONTRACT.md](RUNTIME_CONTRACT.md) | 開発者 | Windows 配布版の `runtime-contract.json`、CPU / CUDA 12.8 lock ファイル、`.local/runtimes/<generation>` の原子的切替と更新手順 | `runtime/runtime-contract.json`, `runtime/requirements-windows.in`, `runtime/requirements-windows-cpu.lock`, `runtime/requirements-windows-cu128.lock`, `scripts/runtime_contract.py`, `scripts/setup.ps1`, `scripts/runtime_activation.ps1`, `src/runtime_dependencies.py` | Active |
| [WINDOWS_BINARY_TRUST.md](WINDOWS_BINARY_TRUST.md) | 開発者 | `SubtitleEditBayLauncher.exe` の静的 CRT（`/MT`）・VERSIONINFO 検証、Authenticode 署名・タイムスタンプの信頼境界 | `launcher/SubtitleEditBayLauncher.c`, `launcher/SubtitleEditBayLauncher.rc`, `scripts/build_launcher.ps1`, `scripts/verify_windows_binary.ps1`, `scripts/sign_windows_artifacts.ps1`, `scripts/windows_signing_identity.ps1` | Active |
| [INSTALLER_MIGRATION.md](INSTALLER_MIGRATION.md) | 利用者 / 開発者 | BAT/ZIP 版から Installer 版への設定・workspace 参照移行、capability 補正、キャッシュ cleanup 計画の仕様と実行手順 | `src/installer_migration.py`, `src/installer_migration_entrypoint.py`, `src/legacy_migration.py`, `src/legacy_migration_inventory.py`, `src/legacy_settings_migration.py`, `src/legacy_cache_cleanup.py`, `scripts/migration_review.ps1`, `scripts/setup.ps1` | Active |

---

## 4. 品質・テスト (`Quality & CI`)

Ruff / mypy（`Any` 禁止）品質ゲート、CI テストグループ分類、PR 検証責務、GUI パフォーマンス計測、実音声 ASR 精度評価の仕様書群です。

| ドキュメント | 想定読者 | 概要（1行） | 正本コード / 関連領域 | 状態 |
| --- | --- | --- | --- | --- |
| [QUALITY.md](QUALITY.md) | 開発者 | `check_quality.py`、Ruff、mypy（`Any` 禁止）、GUI テストハーネス、QML テスト契約、ランチャー／E2E 検証の総合品質基準 | `scripts/check_quality.py`, `scripts/check_no_any.py`, `scripts/check_unittest_discovery.py`, `pyproject.toml`, `tests/gui_test_harness.py`, `tests/media_test_helpers.py` | Active |
| [CI_TEST_GROUPS.md](CI_TEST_GROUPS.md) | 開発者 | `ci_test_groups.json` と `run_ci_tests.py` による CI テスト分類・所有権・変更範囲別ジョブ選択の仕様 | `tests/ci_test_groups.json`, `scripts/run_ci_tests.py`, `scripts/ci_impact.py`, `scripts/check_unittest_discovery.py`, `.github/workflows/ci.yml` | Active |
| [validation-ownership.md](validation-ownership.md) | 開発者 | 通常 CI（`ci.yml`）と `Release readiness`（`release-readiness.yml`）の間での PR 仮マージ commit 検証責務の分担契約 | `scripts/release_readiness.py`, `scripts/release_candidate.py`, `.github/workflows/ci.yml`, `.github/workflows/release-readiness.yml` | Active |
| [GUI_PERFORMANCE.md](GUI_PERFORMANCE.md) | 開発者 | 3,000 件／10,000 件字幕プロジェクトに対する GUI 性能ベンチマーク 8 シナリオ、閾値、CI matrix 運用仕様 | `scripts/run_gui_performance.py`, `scripts/generate_large_gui_fixture.py`, `scripts/compare_gui_performance.py`, `scripts/aggregate_gui_performance.py`, `scripts/plan_gui_performance.py`, `tests/gui_performance_scenarios.py`, `.github/workflows/gui-performance.yml` | Active |
| [TRANSCRIPTION_ACCURACY_CI.md](TRANSCRIPTION_ACCURACY_CI.md) | 開発者 | 実音声 ASR ベンチマーク CI（`transcription-accuracy.yml`）の実行条件、合否基準、キャッシュ仕様と計測記録 | `.github/workflows/transcription-accuracy.yml`, `scripts/benchmark_transcription.py`, `scripts/asr_ci_runtime.py`, `assets/asr_benchmark/manifest.json` | Active |
| [GAMEPLAY_ASR_EVALUATION.md](GAMEPLAY_ASR_EVALUATION.md) | 開発者 | `benchmark_transcription.py` を用いたゲーム実況音声の認識精度・時刻逸脱の評価マニフェスト形式と実行手順 | `scripts/benchmark_transcription.py`, `src/whisperx_runner.py`, `src/transcription_profile.py` | Active |

---

## 5. 作業記録・履歴 (`Archive / Historical`)

完了済み Epic の計画・ロードマップ、段階導入時の中間メモ、特定 PR 時点の監査記録・試行ログ・作業日誌です。
（※ `cutover-403-audit.md` は `tests/test_cutover_audit.py` が検証する新 UI 移行の**監査記録**として分類・保持しています。）

| ドキュメント | 想定読者 | 概要（1行） | 正本コード / 関連領域 | 状態 |
| --- | --- | --- | --- | --- |
| [cutover-403-audit.md](cutover-403-audit.md) | 開発者 | **【監査記録】** 親 Issue #403「新UIモックをproduction UIへ移行する」の完了条件を実装・テスト・CI run へ対応付けた最終監査証跡 | `src/ui/`, `src/gui*.py`, `src/video_sequence.py`, `src/sequence_render.py`, `tests/test_cutover_audit.py` | Historical（監査記録） |
| [archive/QUALITY_SCOPED_FORMAT.md](archive/QUALITY_SCOPED_FORMAT.md) | 開発者 | Ruff format チェックを `scripts/check_quality.py` 単体に限定して段階導入した際のロールアウトノート（正本は `QUALITY.md`） | `scripts/check_quality.py`, `.github/workflows/ci.yml` | Historical |
| [archive/TRANSCRIPTION_CONTEXT.md](archive/TRANSCRIPTION_CONTEXT.md) | 開発者 | Issue #1 Step 1（`transcription_context` の JSON 形状定義のみ）時点の段階ロールアウト計画（正本は `TRANSCRIPTION_DICTIONARY.md`） | `src/transcription_context.py`, `src/transcription_context_config.py` | Historical |
| [archive/TRANSCRIPTION_HINTS.md](archive/TRANSCRIPTION_HINTS.md) | 開発者 | Issue #1 の途中段階として `build_transcription_hints()` 単体を追加した際の中間ステップ記録（正本は `TRANSCRIPTION_DICTIONARY.md`） | `src/transcription_hints.py` | Historical |
| [archive/TRANSCRIPTION_HINT_PLAN.md](archive/TRANSCRIPTION_HINT_PLAN.md) | 開発者 | Issue #1 の途中段階として `transcription_hint_plan.py` を追加した際の中間ステップ記録（正本は `TRANSCRIPTION_DICTIONARY.md`） | `src/transcription_hint_plan.py` | Historical |
| [archive/TRANSCRIPTION_HINT_WORKFLOW.md](archive/TRANSCRIPTION_HINT_WORKFLOW.md) | 開発者 | Issue #1 の途中段階として `transcription_hint_workflow.py` を追加した際の中間ステップ記録（正本は `TRANSCRIPTION_DICTIONARY.md`） | `src/transcription_hint_workflow.py` | Historical |
| [archive/CODEX_EDITING_ROADMAP.md](archive/CODEX_EDITING_ROADMAP.md) | 開発者 | 完了済み Epic #168（子 Issue #169〜#173）の実装順序と完了判定チェックリスト（正本は `CODEX_CHAT.md` / `CODEX_ACTIONS.md`） | `src/codex_runtime.py`, `src/codex_edit_proposal.py`, `src/gui_codex_state.py` | Historical |
| [archive/EDITING_ROADMAP.md](archive/EDITING_ROADMAP.md) | 開発者 | 完了済み Issue #168〜#194 の 4 フェーズ実装順序と当時のリリースゲート計画書 | リポジトリ全体の #168〜#194 各機能 | Historical |
| [archive/CLIPS_KITTY_COMPARISON.md](archive/CLIPS_KITTY_COMPARISON.md) | 開発者 | Issue #440 に際して外部 OSS（Clips Kitty）との機能比較・非流用方針・ライセンス境界を記録した調査メモ | `src/subtitle_export.py`, `src/video_timeline.py`, `src/subtitle_clip_filter.py` | Historical |
| [archive/GAMEPLAY_ASR_TRIAL_2026-09-26.md](archive/GAMEPLAY_ASR_TRIAL_2026-09-26.md) | 開発者 | 2026-09-26 に特定の実況動画 1 本で行った ASR パラメータ比較試行の観察結果ログ（正本は `GAMEPLAY_ASR_EVALUATION.md`） | `src/whisperx_runner.py`, `src/transcription_profile.py` | Historical |
| [archive/CONTEXT_ACTION_BAR.md](archive/CONTEXT_ACTION_BAR.md) | 開発者 | Issue #239 時点における `ContextActionBar.qml` と `CodexSidebarContainer.qml` の配置・操作責務メモ（正本は `GUI_ARCHITECTURE.md` / `workspace-actions.md`） | `src/ui/components/ContextActionBar.qml`, `src/ui/components/CodexSidebarContainer.qml`, `src/ui/screens/MainWorkflowScreen.qml` | Historical |
| [archive/short-mode-design.md](archive/short-mode-design.md) | 開発者 | 初期のショート機能追加時の設計資料および FFmpeg フィルタ図解（現在の状態境界の正本は `SHORT_WORKSPACE.md`） | `src/short_video.py`, `src/short_video_schema.py`, `src/short_video_ass.py`, `src/ui/screens/ShortModeScreen.qml` | Historical |
| [UI_MOCK_ALIGNMENT.md](UI_MOCK_ALIGNMENT.md) | 開発者 | Issue #440 における `ui-redesign-mockup.html` の反映内容、クリップ別字幕絞り込み仕様、残差分と確認手順の記録 | `src/subtitle_clip_filter.py`, `src/gui_subtitles_facade.py`, `src/ui/screens/MainWorkflowScreen.qml`, `src/ui/components/MediaBinPanel.qml`, `src/ui/components/SequenceEditorPanel.qml`, `src/ui/components/WorkspaceInspectorPanel.qml` | Historical |
| [archive/ui-test-review.md](archive/ui-test-review.md) | 開発者 | GUI テスト見直しの初回調査に PR ごとの修正・テスト追加履歴を時系列で累積した作業日誌（正本は `QUALITY.md`） | `tests/test_gui_editor.py`, `src/ui/`, `src/gui*.py` | Historical |

---

## 6. ドキュメント作成・改訂時の共通テンプレート（標準の型）

新規ドキュメントの作成や既存ドキュメントの改訂時は、以下のルールと共通テンプレートに従ってください。

- **ファイル命名規則**: 新規作成・統合先の正本文書は `UPPER_SNAKE_CASE.md` を標準とします（既存テストやワークフローがパスを固定参照している `kebab-case.md` は維持します）。
- **記述言語**: 見出し・本文とも原則として日本語で記述します。
- **索引の更新**: ドキュメントを追加・移動・統合した場合は、必ず本ファイル（`docs/README.md`）の該当カテゴリ表を更新してください。

### 6.1 利用者向けガイドの型（`USAGE.md`, `CONFIGURATION.md`, `CODEX_CHAT.md` 等）

```markdown
# <タイトル>

> - **種別**: 利用ガイド
> - **想定読者**: 利用者（一部 CLI は開発者）
> - **対応機能 / 正本コード**: `<関連する画面名・CLI モジュール名>`
> - **最終確認**: YYYY-MM-DD

## 1. 概要と前提条件
- この機能でできること（1〜3 文）
- 必要な環境・事前準備（Installer 版 / ZIP 版 / FFmpeg / GPU などの要否）

## 2. 基本操作手順（GUI / CLI）
- 画面上の操作ステップ、または CLI コマンド例
- 入出力ファイルと保存先（何を正本として保存し、何が再生成可能か）

## 3. 設定項目・制限事項
- 主な設定キー、既定値、調整の目安（表形式）
- 現在の制限事項・対象外の操作（未実装機能を対応済みと誤認させない境界）

## 4. 受け入れ条件・確認方法
- **利用者による動作・出力の確認手順**:
  - どの表示・出力ファイル・再生結果になれば正常完了と判定できるかのチェックリスト
- **開発・回帰確認コマンド（該当する場合）**:
  - 対応する自動テストや CLI dry-run コマンド
- **異常時の切り分け先**:
  - 失敗時に見るべきログ（システムログ / `*.whisperx.log` 等）と `TROUBLESHOOTING.md` の該当節へのリンク
```

### 6.2 開発者向け（設計・運用・品質）の型（`GUI_ARCHITECTURE.md`, `RELEASING.md`, `QUALITY.md` 等）

```markdown
# <タイトル>

> - **種別**: 設計 / 運用・リリース / 品質・テスト
> - **想定読者**: 開発者
> - **状態**: Active（現行正本） ※履歴文書の場合は `Historical（正本は <リンク>）`
> - **正本コード / スキーマ**: `src/...`, `scripts/...`, `schemas/...`

## 1. 目的とスコープ（非目標）
- この設計・契約が解決する課題
- 明示的に対象外（Non-goal）とする範囲

## 2. 契約・境界と不変条件（Invariants）
- モジュール・Facade・プロセス間の責務分担（表形式）
- データ構造・JSON スキーマ・状態遷移の正本ルール
- 絶対に破ってはならない不変条件（例: fail-closed 条件、元データ非破壊、型 `Any` 禁止など）

## 3. 受け入れ条件・確認方法（Acceptance Criteria & Verification）
- **受け入れ条件（シナリオ / 契約チェックリスト）**:
  - 正常系・競合系・異常系（キャンセル、タイムアウト、ロールバック等）で満たすべき条件
- **ローカル確認コマンド**:
  ```bash
  source runtime/linux-dev/env.sh
  python -m unittest tests.test_<対象モジュール>
  python scripts/check_quality.py --lint-only
  ```
- **CI ゲート / 所有グループ**:
  - `tests/ci_test_groups.json` の所属グループ（`portable-unit` / `qt-gui` / `ffmpeg-runtime` / `windows-*`）および対応する GitHub Actions ワークフロー

## 4. 関連ドキュメント
- 上位・下位の設計書、利用ガイド、過去の経緯（`docs/archive/...`）へのリンク
```

### 6.3 作業記録・アーカイブ文書のヘッダー型（`docs/archive/` 配下）

アーカイブへ移す文書（または履歴として残す文書）は、内容を消さずに冒頭へ以下の Callout を付与し、読者が古い仕様を現行正本と取り違えるのを防ぎます（リンク先は `../SHORT_WORKSPACE.md` のように正本文書への実在する相対パスを指定します）。

```markdown
> [!NOTE]
> **履歴資料（Archive）**: この文書は Issue #XXX / PR #YYY 時点の計画・作業記録です。
> 現在の正本仕様は `docs/` 直下の正本文書（例: [SHORT_WORKSPACE.md](SHORT_WORKSPACE.md)）を参照してください。
```
