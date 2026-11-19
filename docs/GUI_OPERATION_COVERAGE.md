# GUI操作と自動テストの対応監査

対象: Subtitle Edit Bay `main`、`0251cc8507c996db961db8a8b804d9c031808752`。この資料は**既存テストが何を検証するよう書かれているか**のソース監査。現在のGUIで各操作を新規実行した結果ではない。対象外: HTMLモック、CLI単独操作、OSのネイティブダイアログ内操作、インストーラー単独操作。調査中の項目と「存在しない操作」を未検証と混同しない。

## 判定の読み方

| 判定 | 根拠 |
| --- | --- |
| 実入力＋結果 | 対象コントロールへのQtクリック、キー、ドラッグ等を送信し、その操作固有の状態・データ・出力をassert |
| 途中から＋結果 | QMLシグナルを直接発火、プロパティを直接セット、またはFacadeを呼び出し、その先の結果をassert。見えて押せることやマウスのヒット判定は未保証 |
| 静的／状態のみ | QML構造、表示条件、enabled、接続などのみ。操作後の結果までは検証しない |
| 根拠未発見 | 確認範囲では対象経路を検証するテストを特定できなかった。テスト不存在の証明ではない |

保存・再読込、ジョブ処理中、キャンセル、入力不正、繰り返しは、関係するものだけ通常系から独立して判定する。同じ処理でも、ボタン・ショートカット・ドラッグなど異なる入口を一括合格にしない。`tests/gui_test_harness.py` の `click/click_at` は可視・有効・寸法を確認後に `QTest.mouseClick` を送る。一方 `emit_signal` は実ハンドラを動かすが入力経路を飛ばす。セットアップのための直接呼び出しと、検証対象操作の直接呼び出しも区別する。

## どこまで洗い出したか

全44 QMLファイルを走査し、入力・中継ハンドラ候補343箇所、固定 `objectName` 381種、関連しうるテストメソッド候補302件を抽出。**候補の件数であり、操作数・合格数・網羅率ではない**。同一操作を中継する複数イベント、プログラム発火、動的生成、テスト間接呼び出しがあるため、人が操作単位に正規化する。以下は主要経路を手で照合した初版で、アプリ全体の網羅率は算出しない。付属スキャナーは候補出し専用であり、文字列一致をカバレッジとして扱わない。

## 次に埋める操作

最初のテストPRは、**タイムライン上で範囲を実ドラッグし、その範囲をカットとして追加する経路**に絞る。既存ケースはQMLヘルパーに範囲を渡すため、ドラッグ入力・時刻変換の欠落を検出できない。確認するのは、①通常・逆向きドラッグの開始／終了、②短いクリックを範囲選択にしないこと、③追加（選択範囲・保存データ）とUndo、④処理中は既存範囲と履歴を変えないこと。既存のクリック・Undoケースを置き換えず、重複するassertは共有可否を確認する。

別枠の候補は素材一覧のURLドロップ。ウィンドウ全体の素材ドロップや素材カードからのドラッグは別経路。素材一覧のdrop領域へ `QDragEnterEvent` / `QDropEvent` を送り、対象パス・件数・無効入力・処理中の拒否まで見る。これはOSの外部ドラッグ全体の保証とは区別する。

既に実入力から結果を確認している字幕削除・履歴・保存、フェーダーのドラッグ、ミキサーのリセット、AI提案破棄を、単純に追加候補にはしない。
## プロジェクト・字幕・書き出し

|優先度 / 操作|UI→実処理|既存の具体テストと操作方式|検証される結果・境界|
|---|---|---|---|
|P0 新規動画編集開始|`ProjectStartScreen.qml` `newVideoEditButton` → `ProjectStartFlow.startNewVideoEdit()` → `browseVideoFile/createEmptyProject/loadProject`|`test_new_video_start_action_creates_empty_project_and_opens_workspace` (`test_gui_editor.py`): 実クリック、ファイルダイアログをpatch|新規空プロジェクトが生成され、プロジェクトパス・画面・字幕モードを確認。|
|P0 既存プロジェクトを動画選択から開く|同上 → `transcriptionProjectExists/loadProject`|`test_new_video_start_action_opens_existing_project_for_selected_video`: UI実クリック、source/project fixture|既存字幕と保存先動画が復帰。|
|P0 音声素材の追加・削除・全消去|`SourceSettingsPopup.qml` `sourceAudioAddButton`, `sourceAudioRemoveButton-*`, `sourceAudioClearButton` → `browseAudioFiles/removeAudioFile/clearAudioFiles`|`test_source_audio_add_remove_clear_buttons_save_selected_sources`: GUI実クリック、ファイル選択patch|一覧とsource stateの追加/削除/空状態、および確定後のプロジェクト保存を検証。|
|P0 ソース設定の確定・キャンセル|`sourceDoneButton`/`sourcePopupCloseButton` → QMLハンドラからsource state apply/discard|`test_source_popup_close_discards_pending_media_and_preserves_edits`: GUI実クリック、ファイルダイアログpatch|閉じる時は未確定メディアを破棄し、編集中project/history/diskを保持。|
|P0 字幕追加（再生位置）|`SubtitleWorkspaceEditor.qml` `workspaceSubtitleAddButton` → `performSubtitleEdit("add", playhead)`|`test_workspace_subtitle_mode_adds_first_caption_at_shared_playhead`: 実クリック、playheadをbackendで設定|空リストに字幕を追加し、開始時刻が2.5秒、編集欄が表示される。|
|P0 字幕本文入力|`SubtitleModeSettings.qml` `workspaceSubtitleTextArea` `onTextChanged/beginDraft/commitCaptionText` → editor state/controller|`test_new_video_gui_journey_saves_reloads_and_renders_caption`: UIクリック＋実キー入力|入力本文の保存、再度開いたprojectへのロード、後続renderまでend-to-end。|
|P0 字幕選択・時刻入力|`workspaceSubtitleStartField/EndField` → `beginTimeEdit/updateTimeDraft/commitTimeEdit` → subtitle facade|`test_workspace_subtitle_time_speaker_font_and_size_are_saved`: 実クリック＋キー入力、ComboBox keyboard|時刻・話者・font・size更新が保存される。フィールドdraft/確定の完全境界は別の入力待機テストも存在。|
|P0 字幕削除・Undo・Redo・保存|`workspaceSubtitleDeleteButton/UndoButton/RedoButton/SaveButton` → `performSubtitleEdit/saveProject`|`test_workspace_subtitle_delete_undo_redo_and_save_round_trip`: GUI実クリック|削除後の件数/選択/ボタン状態、undoで復元、redoで再削除、保存・reloadを確認。|
|P0 Undo後の新規操作でRedo無効化|`workspaceSubtitleAddButton` → shared edit history|`test_workspace_subtitle_new_edit_after_undo_discards_redo`: 実クリック、playhead stateを設定|新規字幕追加でredo不可となり、再undoで追加分だけ戻る。|
|P0 保存失敗と再試行|`workspaceSubtitleSaveButton` → save handler/backend|`test_workspace_subtitle_save_failure_preserves_disk_and_allows_retry`: GUIクリック、保存関数を失敗注入|ERROR/status、dirtyとメモリ編集維持、元ファイルbytes不変、再試行成功。|
|P0 プロジェクト保存後の別プロセス再読込|Header Save / project persistence controller|`test_project_save_restart_reload_e2e_preserves_edits_and_unsaved_switch`: UIクリック、別Python probe subprocess|保存済み時刻・話者・スタイルが新プロセスreloadで保持、未保存更新のswitch時挙動も検証。|
|P0 字幕の実書き出し|expanded editor `editorRenderButton` → render handler/workflow|`test_editor_render_e2e_saves_edits_and_burns_subtitles`: GUIクリック・キー入力、ffmpeg実行|編集内容と時刻が保存される、出力ファイル非空、フレーム差で字幕焼付を確認。|
|P1 既存projectの切替時にpending edits保存|`projectOpenButton` → `browseProjectFile/loadProject`|`test_load_project_saves_pending_changes_before_switching`: GUI実クリック|切替前に保存される。保存失敗時の切替拒否は `test_load_project_refuses_switch_when_save_fails`。|
|P1 project Save As|Source settings `projectSaveAsButton` → save-as dialog/backend|`test_save_as_preserves_export_and_waits_for_pending_autosave`: backend facade直接呼出し（GUI入力のテストではない）|最新autosave revisionが新pathへ書かれ、export dir/history保持、旧path非変更、失敗時projectPath維持。`test_export_change_is_visible_and_saved_before_source_popup_closes` では実クリック＋保存ダイアログの戻り値をstubし、新しいファイル・プロジェクトパスと出力先をassert。ネイティブダイアログ自体や入力不正の操作は別。|
|P1 ソースファイルのウィンドウdrop|Main screen DropArea → video/audio classification|`test_window_drop_area_imports_source_and_disables_during_processing`: Qt drag/drop eventを送信|video source反映、processing中無効。通常マウス操作の実ドラッグとは異なる合成イベント。|
|P1 ソース設定内video drop|`SourceSettingsPopup.qml` `sourcePopupDropArea` → video selection|`test_source_popup_drop_target_imports_video`: Qt QDragEnter/Drop event|accept/drop、video path反映、実際のOS drag UIは未実施。|
|P1 字幕分割と境界拒否|`workspaceSubtitleSplitButton` → `performSubtitleEdit("split", playhead)`|`test_workspace_subtitle_split_uses_playhead_and_rejects_boundaries`: 実クリック、playheadをAPI設定|境界位置は無効・状態不変、中間点は元本文を保持して二分、undoで復元。|
|P1 字幕タイムライン移動|`SubtitleTimeline.qml` clip drag → `seek/selection/timing update`|`test_subtitle_timeline_drag_is_locked_during_processing_and_recovers`: QTest mouse press/move/release|processing時は非編集、ドラッグしても開始時刻不変。解除後のドラッグで時刻変化。|
|P1 字幕タイムラインの端トリム|`timelineCaptionStartHandle/EndHandle` drag|`test_subtitle_timeline_resize_is_locked_during_processing_and_recovers`: QTest mouse drag|processing中の開始/終了時刻不変、解除後のresize動作を検証。|
|P1 字幕プレビュー設定|`buildSubtitlePreview(settings)` → facade/ASS preview builder|`test_preview_updates_project_settings_and_ass_path`: backend method直接呼出し（UI handlerを通さない）|設定値がproject `subtitle_settings` とASS preview pathに反映。さらに `test_workspace_caption_key_input_is_committed_before_preview` はGUIクリックでASSを生成し、未確定入力した本文を出力に確認。|
|P1 通常render時のworkspace保持|Context/header render actions → workflow preflight/progress|`test_both_render_actions_share_preflight_progress_and_preserve_workspace`: backend `renderVideo/renderShortVideo`直接呼出し、process finishを注入|active job、codec選択、progress、編集mode/playhead保持。UIクリックによるhandler確認は別のexpanded editor E2E。|
|P1 UI renderで出力先未設定|Header Render → select output → render|`test_new_video_gui_journey_saves_reloads_and_renders_caption`: GUI実クリック、directory dialog patch、ffmpeg実行|出力先選択、project保存先と出力先の分離、render完了と非空artifactを確認。|
|P1 Render preflight失敗|Render action → missing ffmpeg guard|`test_render_preflight_rejects_missing_ffmpeg_without_starting_process`: backend直接呼出し、dependency state設定|ffmpegなしではprocess開始せず、エラーにffmpegを示す。|
|P2 Import処理中drop拒否|drop handler|`test_drop_rejects_sources_while_processing`: drag/drop event合成|running中は拒否されsource path不変。通常条件の境界回帰。|
|P2 クリップ字幕絞り込みと履歴|`workspaceSubtitleClipFilter`及び字幕一覧filter|`test_subtitle_clip_filter_survives_edits_history_and_saving`: Facade直接。GUIの絞り込み変更は別の `test_subtitle_clip_filter_qml_maps_rows_and_excludes_other_assets`|filter保持と編集/Undo/Redo/保存の相互作用を対象。通常字幕CRUDとは別の機能。|

|P0 新規文字起こし開始（ホーム）|`startWithTranscriptionButton` → `ProjectStartFlow.startTranscription()` → `workflow.startTranscription`|`test_transcription_gui_process_creates_and_loads_project` の実クリック＋模擬子プロセス|`EDIT`到達、進捗・ファイル・字幕をassert。実ASR精度とは別。ソース不足は `test_start_screen_transcription_opens_source_setup_when_sources_are_missing`。|
|P1 本文編集をUndo/Redo|`workspaceSubtitleTextArea` と `workspaceSubtitleUndoButton/RedoButton` → 作業中の本文を履歴へ|`test_pending_text_undo_redo_survives_save` の実キー・クリック|Undo後の旧本文、Redo後の新本文を保存JSONでassert。|

### この範囲の注意

- 既存テストは多数が実GUI実クリック/実キー入力を使うが、いくつかはbackend facade/stateを直接呼び出す。表で明記した通り、直接呼出しをUI操作の証明として混同しない。
- `QMetaObject.invokeMethod(..., "clicked")` は信号を直接発火させるテストもある。該当する場合は実クリックと表現しない。本表のsource settings内部の一部検査はこれに該当するが、追加/削除/確定の対象テストは `_click` を使う。
- GUI本体の広い操作カバレッジは `tests/test_gui_editor.py` に集約され、project editorの純backend履歴契約は `tests/test_gui_project_editor_controller.py` にもある（例: `test_segment_crud_move_selection_and_undo_redo` はcontroller-levelでUI操作ではない）。
- 字幕行単独クリックから選択・別の行の非変更を確認する経路、Save Asダイアログ自体のOS操作は、この範囲では未確認。**テストなしと断定せず、本監査で未確認**とする。
- この監査ではテスト実行なし。先行調査で `python -m unittest tests.test_qml_static` を試した際、16テスト中15通過し、qmllint依存不足 (`pyside6-qmllint is required with PySide6`) で失敗した。これはその実行時点の情報であり、今回の網羅性検証として扱わない。
## 素材・シーケンス・カット・ミキサー

「GUI/QTest」は Qt Quick item を objectName で取得してクリック／ドラッグ等を送る実 UI 経路（テスト内で一部 `setProperty` / QML helper も併用）。「Facade」は backend API を直接呼ぶ。「Static」は QML文字列・構造確認のみ。永続性欄は reload / project file の assertion がある場合に限り記載。

| # | 具体操作、QML入口 → backend | 既存テストと期待結果(assertion) | 検証種別・永続性・信頼度 |
|---|---|---|---|
| 1 | 素材一覧の「追加」`mediaBinAddButton` → `sequence.browseSequenceAsset()` | `test_media_bin_add_button_imports_asset_and_saves_from_screen`: ダイアログ選択、asset count 2。Save後 project sequence.assets に2件/path一致 | GUI click、dialog/probeをpatch、保存ファイル確認。高 |
| 2 | 素材カードの＋ `addSequenceClipButton` → `addSequenceClip(id)` | `test_main_workflow_sequence_panel_reuses_gui_session_and_dispatches_actions`: card出現、追加、undo/redoで数が戻る/再追加 | GUI click + item property探索、保存の明示確認なし。同テストとFacade。高 |
| 3 | media bin URL drop `mediaBinDropArea` → `addSequenceAssets(urls)` | 専用の実drop結果 assertion は見当たらず | Static（`test_sequence_editor_uses_backend_view_and_mutation_boundary`）とGUIで領域の存在確認（`test_main_workflow_sequence_panel_reuses_gui_session_and_dispatches_actions`）。**優先ギャップ**: URL型/複数/不適格URLの実drop未カバー。低 |
| 4 | 素材カードをタイムライン空き領域へ drag/drop `mediaAssetDragArea` → `insertSequenceClip(assetId,index)` | `test_media_bin_drag_inserts_clip_before_drop_target`: QTest press/move/release、2 clips、undo/redo、save+reload後assetId維持 | GUI実drag、backend状態、保存/reload。高 |
| 5 | 素材カードを配置済み clip の前へ drop `sequenceClipDropArea` → `insertSequenceClip` | `test_media_bin_drag_inserts_before_clip_and_appends_after_last`, `test_media_bin_drag_onto_clip_card_inserts_before_it`: 並び順を確認 | 実QTest drag。後者はカードdrop領域。高 |
| 6 | clip card reorder drag / cancel `DragHandler`, `sequenceClipDropArea` → `moveSequenceClip` | `test_sequence_clip_card_drag_reorders_before_target`:順序変化。`test_sequence_clip_card_drag_cancel_restores_position` と `...waits_for_pending_layout`: cancel後順序/全cliplists同一 | QTest drag、cancel含む。高 |
| 7 | タイムライン中央 drag reorder `sequenceTimelineMoveArea-<id>` → `moveSequenceClip(id,targetIndex)` | `test_sequence_timeline_drag_trims_and_reorders_clips`: move後の先頭clip ID確認 | QTest実drag、モデル状態。高 |
| 8 | タイムライン左端 trim `sequenceTimelineTrimStart-<id>` → `trimSequenceClip(id,start,end)` | 同上: startを約1.0sへ移動、undoで0に戻る | QTest実drag + undo assertion。高 |
| 9 | タイムライン右端 trim `sequenceTimelineTrimEnd-<id>` → `trimSequenceClip` | 同上: end縮小、undoで元に戻る | QTest実drag + undo。高 |
| 10 | playhead seek slider `sequencePlayheadSlider.onMoved` → `setSequencePlayhead(ms)` | `test_sequence_playhead_and_zoom_sliders_follow_drag`: slider dragで outputMs >= 4000 | GUI item sliderをdrag、backend値 assertion。保存対象ではなく再生位置。高 |
| 11 | sequence zoom `sequenceTimelineZoomSlider` → `setSequenceZoom`, 50–250% clamp/10 step | 同上: zoom in/outでclip widthが大/小 | GUI操作、layoutの視覚寸法 assertion、backend非対象。高 |
| 12 | clip card選択/seek `TapHandler` → `setSequencePlayhead(outputStart)` | `test_sequence_remove_button_undo_redo_and_save_from_screen` を含む card GUI群。timeline clip click相当はmove-area clickでseek。 | QMLは明確だが個別で純粋なTapHandler click coverageは限定的。clip list/Facadeに類似。中 |
| 13 | clip 削除 `removeSequenceClipButton` → `removeSequenceClip(id)` | `test_sequence_remove_button_undo_redo_and_save_from_screen`: GUI削除、undo/redo、save後 project clips件数 | GUI click + 履歴 + disk。高 |
| 14 | 数値入力 trim start/end `sequenceClipStartField` / `sequenceClipEndField` → `trimSequenceClip` | `test_sequence_time_typed_without_return_is_saved_from_header`: text入力をheader Saveでcommit、model/file値を比較。invalid時UI resetはQMLで実装 | GUI text/Saveと永続化。invalid値の画面経路は独立未確認。中-高 |
| 15 | transition type/duration `sequenceTransitionCombo`, `sequenceTransitionDuration` → `setSequenceTransition` | `test_sequence_transition_controls_from_card_are_saved`: combo選択fade、duration 0.5s、saved project transition一致 | GUI click/modified signal + save。高 |
| 16 | clip音声リンク、volume、mute、offset `sequenceAudioLinkedCheck`, `sequenceClipVolumeSlider`, `sequenceClipMutedCheck`, `sequenceAudioOffset` → `setSequenceClipAudio` | `test_sequence_audio_controls_from_card_are_saved`: linked false、mute true、slider/offset更新、project保存値確認 | GUI click/slider; volumeではslider valueをsetPropertyし moved signalをinvokeする箇所あり。永続化。中-高 |
| 17 | sequence全体 undo/redo `sequenceUndoButton` / `sequenceRedoButton` → subtitles history | `test_main_workflow_sequence_panel_reuses_gui_session_and_dispatches_actions`, `test_sequence_remove_button_undo_redo_and_save_from_screen`。また `test_sequence_edits_use_controller_history_and_persist_in_order` はFacade/controller | GUI + backend、状態/順序。高 |
| 18 | invalid/busy insert rejection → `insertSequenceClip` | `test_sequence_insert_at_index_is_atomic_and_rejects_invalid_or_busy_edits`: -1/99とrunning中 false、sequence不変。`test_sequence_asset_validation_fails_closed`: missing/zero durationの追加拒否とerror | Facade直接呼び、UI busy disableや不正入力実操作ではない。高(backend) / 低(UI) |
| 19 | カット範囲をtrack上でdrag選択、短 clickでseek `workspaceCutTimeline` → `rangeSelected` / `seekRequested` | `test_workspace_cut_mode_adds_and_undoes_a_selected_range` は `_qml_call(setCutSelection,...)` で範囲設定後GUI add click。track drag自体は直接送らず | UI clickとQML helper。別テストでタイムラインのclick／選択解除を検証するが、実drag未確認。**優先ギャップ**。中低 |
| 20 | カットの追加/変更、restore/clear、undo/redo `addCutButton`, `restoreCutRangeButton`, `clearCutsButton` → `workspace.addCut/updateCutRange/restoreCutRange/clearCuts` | `test_workspace_cut_mode_adds_and_undoes_a_selected_range`, `test_workspace_cut_settings_follow_undo_redo_and_merged_boundaries`, `test_cut_restore_and_clear_buttons_update_history_and_saved_project`; `test_cut_restore_button_requires_an_overlapping_range` | 設定はqml helper/Facade、一部GUI click。保存ファイル確認、無効範囲button disabledを確認。cut timelineのhit-testより設定面中心。高 |
| 21 | 字幕clip選択/移動 `timelineCaption-<index>` / moveArea → `selectSegment`, `moveSegment` | `test_subtitle_timeline_drag_is_locked_during_processing_and_recovers`: Qt mouse press/move/release、running中不変、解除後start増加。snap単体は`test_timeline_move_and_resize_snap_to_grid_and_neighbor_edges` | GUI実drag + 処理中lock + Facadeのsnap assertion。保存/reloadはこのケースでは未確認。高 |
| 22 | 字幕開始/終了handle resize `timelineCaptionStartHandle`, `timelineCaptionEndHandle` → `resizeSegmentStart/End` | `test_subtitle_timeline_resize_is_locked_during_processing_and_recovers`: running中両端不変、解除後それぞれ変化 | 実QTest drag、busy/recovery。保存は別系統。高 |
| 23 | mixer channel mute/solo/enable/fader `mixerMuteButton`, `mixerSoloButton`, `mixerChannelEnabledCheck`, `mixerChannelFader` → channel changeRequested / `updateAudioMixChannel` | `test_audio_mixer_gui_settings_are_saved_and_applied_to_rendered_output`: UI mute/solo/enable、fader moved signal、保存された設定、render audio比較。`test_audio_mixer_updates_individual_source_and_resets` はFacade API + save/reset | renderのテストではフェーダーはシグナル直発火。別の `test_mixer_fader_drag_reaches_target_and_saves` は実ドラッグを送り、途中未確定・リリース後変化・保存JSONをassert。 |
| 24 | mixer reset `mixerResetButton` → `resetAudioMixer()` | `test_mixer_reset_button_restores_and_saves_defaults_after_edit`: 処理中のクリックは既存設定を保持、処理解除後のクリックで初期値に戻る | GUIクリック、busy解除、保存後JSON一致。高 |

### この範囲の優先順位

1. **最優先: mediaBin URL drop と cut timeline range drag**。QML handlerはあるが対応する実際のpointer/dropを通す期待 assertion が読み取れるテストにない。特に drop acceptance、drop.cancel、境界座標、範囲逆方向/短すぎをUIから確認する。
2. **次点: invalid/busyをUI入口から試す**。sequence facadeのatomic rejectionは確認済みだが、`running`時の各Button/DropArea/MouseArea disabledと無効時間入力のrevertは一部静的/バックエンド止まり。sequence timeline trim/reorderのbusyは未確認。字幕timelineのbusy/recoveryは既に強い。
3. **字幕timeline seek / lane/scroll / drag snapping**。visible caption生成には `test_qml_timeline_instantiates_only_visible_captions`、snapはFacade test、move/resize busyは実dragである一方、タイムライン背景クリックからseekと選択後のhandle操作を一続きで検証するケースは限定的。
4. **音声ミキサーは重複追加不要**。実ドラッグ＋保存、リセット実クリック＋busy＋保存、音声レンダリング結果を、別々の経路で検証する既存テストがある。
5. **キャンセルと保存**。sequence card drag cancel、media-bin insert undo/redo/save+reload、remove save、trim typed save、audio/transition saveが個別に存在。すべての操作ごとに保存/reloadがあるわけではなく、永続化未assertを「保存確認済み」と扱わないこと。

## ショート・AI・設定

### Short workspace

| UI / handler | backend / 保存経路 | UIテスト・assertion |
|---|---|---|
| `workspaceHeaderShortButton` → `openShortWorkspace()` / `shortModeBackButton` → `closeShortWorkspace()` (`ShortModeScreen.qml`) | workspace切替。専用 `shortPreviewPlayer` と通常プレイヤー状態を分離 | `test_short_mode_screen_opens_and_closes`: Qtクリックで可視状態。`test_new_shell_short_workspace_restores_normal_player_and_isolates_preview`: player独立、通常位置復帰をassert。 |
| `shortModeGlobalFitCombo.onActivated` | `shortVideo.setShortVideoGlobalFit` → `_commit_short_video` | `test_short_mode_settings_controls_save_round_trip`: Qtクリック+Down/Returnで`contain`、保存後JSONをassert。 |
| `shortModeBackgroundColorField` / `shortModeBackgroundColorButton` / dialog | `setShortVideoGlobalBackgroundColor`; draftは `commitPendingEdits` で検証後commit | roundtrip testは背景色の保存を確認。`test_short_export_waits_for_incomplete_background_color`, `test_short_export_rejects_incomplete_color_after_focus_moves`, `test_short_background_color_survives_volume_change_before_return` は不完全値保護。色ダイアログの成功経路はUI操作テストで個別確認が必要。 |
| `shortModeTransitionCombo.onActivated` | `setShortVideoTransition(type,duration)` | roundtrip testでQt combo操作後`fade`をassert。 |
| `shortModeTransitionDurationSlider` drag/key | `setShortVideoTransition` | `test_short_mode_transition_duration_uses_internal_values` は3 transitionでdrag後内部値を確認。`test_short_mode_sliders_follow_full_drag_and_save`: Qt drag、Undo/Redo/Left、保存JSONをassert。 |
| `shortModeSubtitleScaleSpin.onValueModified` | `setShortVideoSubtitleScale` | roundtrip testでUpキー後151、保存JSONでも151。 |
| `shortModeBgmBrowseButton.onClicked` | `browseShortModeBgm()` → QFileDialog → path保存 | roundtrip testはdialog関数をpatchしQtクリック、呼出一回とpathをassert。OSネイティブdialogはmock。 |
| `shortModeBgmIn/Out/StartField.onEditingFinished` | `commitPendingEdits` → `setShortVideoBgm({in,out,start})` | roundtrip testで各TimeFieldへQt入力+Return、内部値と保存JSONをassert。`test_short_export_saves_bgm_time_typed_without_return`: Returnなしでもexport前commit。 |
| `shortModeBgmVolumeSlider` drag | `_sendBgmUpdate({volume})` → `setShortVideoBgm` | roundtrip + sliders test: drag、Undo/Redo/Left、保存roundtrip。`test_short_bgm_time_survives_volume_change_before_return` は編集中時刻draft保持を確認。 |
| `shortModeClipSourceCombo`, `shortModeSegmentCombo` | `subtitles.subtitleModel`; 追加でsegment id選択 | `test_short_mode_segment_picker_uses_the_subtitle_model`: Comboをクリック+キー操作し選択表示名/idと追加結果をassert。 |
| `shortModeRangeStart/EndField`, `shortModeAddClipButton.onClicked` | `addShortVideoClipByRange(start,end)` | `test_empty_short_mode_gui_adds_range_clip_and_enables_export`, `test_short_mode_gui_adds_direct_range_clip_when_segments_exist`: Qt入力/クリック後start/end、segment_id空を確認。 |
| delegate `shortModeStartTimeFieldN` / `EndTimeFieldN` | `updateShortVideoClip(index,changes)`; 不正 draftは残す | `test_short_export_saves_clip_time_typed_without_return`, `test_short_back_commits_clip_time_typed_without_return`: Returnなし入力をexport/back時commit。`test_short_incomplete_clip_time_blocks_export_after_focus_moves`, `...survives_list_scroll`, `...waits_for_incomplete_clip_time_and_retries`: 入力保持、disabled export/back、再入力再試行。 |
| delegate `shortModeFitComboN.onActivated` | clip単位fit更新 | `test_short_mode_fit_combo_updates_its_delegate_clip`: virtualized listをスクロール、4番目delegateのcomboをQt操作しindex 3だけ変更をassert。 |
| `shortModeMoveUp/DownButtonN`, `shortModeDeleteButtonN` | 並べ替え・削除 facade | `test_short_clip_time_stays_with_clip_when_reordered_before_return`, `test_short_clip_time_is_saved_before_deleting_another_clip`, `test_short_clip_reorder_waits_for_incomplete_time`: Qt click後のdraft・削除・不完全入力拒否。 |
| `shortModeExportButton.onClicked` | `commitPendingEdits()`後 `workflow.renderShortVideo()` | `test_short_mode_gui_export_e2e_renders_vertical_video_audio_and_subtitles`: Quick UIからrender E2E。入力不完全拒否は上記export関連テスト。 |
| `shortModePreview` / `shortPreviewPlayer` | clip選択で `syncClipPlayback`; 専用playerをsource timeにseek/play | `test_short_mode_clip_list_and_preview` は選択/preview状態。shellテストは通常player非干渉。映像画素の視覚比較ではない。 |

### AIチャット / 提案カード

| UI / handler | backend path | UIテスト・assertion |
|---|---|---|
| `codexChatToggleButton` | 認証時だけenable、`panel.expanded`変更 | `test_codex_sidebar_follows_authentication_and_survives_workspace_changes`, `test_codex_auth_controls_fit_and_dispatch_from_screen` は可視・認証・操作を確認。 |
| `aiProviderHeaderCombo.onActivated` | `backend.ai.selectAIProvider` | `test_codex_model_and_new_chat_controls_preserve_project`: Quick combo操作でprovider変更、project/undo/revision/file bytes不変。Gemini routeを保つテストもあり。 |
| `codexModelCombo` | 選択modelをprovider stateへ | 同テストはQuick combo変更、選択モデルとproject不変をassert。 |
| `codexNewChatButton` | `startNewCodexChat()` | 同テストがQtクリックし新規chatと既存proposal/projectの保全を検査。 |
| `codexChatInput` + `codexChatSendButton` | `sendCodexChatMessage(message,scope,start,end)` | `test_subtitle_chat_uses_the_typed_proposal_path_instead_of_plain_codex` はfacade dispatch境界を直接確認、字幕提案はplain chatではなくtyped proposal。`test_audio_chat_natural_language_uses_typed_audio_proposal_path`も同様。別途 `test_ai_typed_audio_proposal_works_without_chat_model` と `test_ai_rejected_typed_actions_keep_draft` で実クリック→stub dispatch・下書き保持／エラー状態を確認。実ネットワークではない。 |
| `codexChatEditScope`, `codexChatRangeStart/End` | send argsの編集対象範囲 | typed proposal testでautoが安全なselected scopeになることをassert。各scope選択からsendまでの網羅GUI経路は確認できず。 |
| `codexChatStopButton` | `stopCodexChat()` | `test_progress_and_codex_controls_remain_clickable_together` はQtクリック→stubへのstop呼出を確認。実稼働中の停止完了・再送の一連は未確認。 |
| `codexProposalList` + `codexOperationCheck.onToggled` | `selectedOperationState` local更新 | `test_new_codex_proposal_reselects_reused_operation_id` はQtクリックで選択解除・ボタン無効化、同IDの新提案で再選択をassert。 |
| `codexApplyButton.onClicked` | `applyCodexProposal(ids)` / audioなら `applyAudioMixProposal(ids,false)` | `test_ai_proposals_are_locked_during_processing_and_recover` で音量提案の処理中ロック、再選択→GUI適用→音量110%を確認。複数字幕操作の部分適用→Undo→再読込は別シナリオとして未確認。 |
| `codexDiscardButton.onClicked` | `discardCodexProposal()` / audio discard | `test_new_codex_proposal_reselects_reused_operation_id` でQtクリック→リスト0件、`test_ai_proposals_are_locked_during_processing_and_recover` で字幕案の消去と履歴・revision・disk不変をassert。 |
| `codexAudioAllowSilenceButton` | `applyAudioMixProposal(ids,true)` | `test_audio_proposal_requires_explicit_click_to_mute_every_output`, `test_audio_mix_proposal_with_no_selected_operations_is_rejected` は安全条件。前者は通常適用拒否→専用ボタンの実クリック→全ミュート・JSON保存までassert。 |
| `codexReloginButton`, `codexLogoutButton` | `reloginAIProvider()`, `logoutAIProvider()` | `test_codex_auth_controls_fit_and_dispatch_from_screen` は画面からの操作dispatchを確認。 |

### 設定・復旧

- `settingsToggleButton` / `settingsPopupSaveButton` → QML settings snapshot → backend settings保存。`test_qml_settings_round_trip_and_expanded_popup_fit` はQt click、control更新、保存後backend値をassert。`test_settings_reject_blank_numeric_draft_and_allow_retry` は不正draftと再試行を検査。Short設定のproject persistenceはShortのroundtripテストでJSON再読込確認。
- `src/project_recovery.py` / `project_snapshots.py` backendは存在するが、`src/ui`に復旧control/handlerを確認できず、復旧の独立したGUI操作としては数えない。自動復旧は別途起動フローとして定義して照合する。

### 優先ギャップ

1. **字幕提案の部分適用**。選択・破棄・音量案の適用は実クリックで検証済み。複数字幕操作のうち一部だけ選択し、他の字幕を変えないこと・Undo・再読込まで通すケースは、この範囲で未確認。
2. **Chat停止後の復帰・再試行**。クリックから停止要求、送信拒否時の下書き保持とエラー状態は既存。一連の復帰・再送や視覚表示は別。
3. **復旧UI**。現状のQMLから入口を見つけられない。ユーザー復旧が仕様なら、UI動線と異常終了後のシナリオを確認。
4. **Short preview視覚QA**。player状態はassertされるがfit/background/overlayの画像比較は未確認。
5. **setter失敗の通知**。一部draft保持はあるが、色/設定setter失敗時にユーザー向けエラー状態が表示されるかの検査は薄い。

## 次回更新の手順

1. 画面、操作、入力経路（ボタン／キー／ドラッグ等）、適用条件を一意に記録する。見た目だけの切替と、データを書き換える操作を分ける。
2. `objectName` とハンドラから、画面→中継シグナル→Facade/Backendまで追う。テストの入力、操作直後のassert、永続化のassertを個別に見る。
3. 最初にデータ消失・誤書き出し・別対象への変更を拾い、次にキャンセル・処理中・入力不正を埋める。UI入力を追加するだけで済むか、仕様の確定が先かを分ける。
4. 操作一覧と分母を確定した後だけ、判定可能な行について「実入力＋結果を持つ操作数 ÷ 対象操作数」を出す。未照合、対象外、異常系のみ、手動確認は別集計とする。数字とともに対象コミットを残す。

検証状態: この資料の作成ではソースの照合と候補抽出を実施。Qtランタイムテスト、Windowsネイティブダイアログ、実ファイル入出力の新規実行は、この資料の合否としては計上していない。
