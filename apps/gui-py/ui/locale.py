"""多语言支持：中文、英文、日语、德语、法语、文言文（6 语言）。"""
from __future__ import annotations

from enum import Enum

class Lang(Enum):
    ZH = "zh"      # 中文
    EN = "en"      # English
    JA = "ja"      # 日本語
    DE = "de"      # Deutsch
    FR = "fr"      # Français
    WY = "wy"      # 文言文

_LANG_NAMES = {
    Lang.ZH: "中文",
    Lang.EN: "English",
    Lang.JA: "日本語",
    Lang.DE: "Deutsch",
    Lang.FR: "Français",
    Lang.WY: "文言文",
}

def lang_name(lang: Lang) -> str:
    return _LANG_NAMES.get(lang, "中文")

# 翻译表
_T = {
    # 通用
    "brand":            {Lang.ZH: "DeepSeek Harness", Lang.EN: "DeepSeek Harness", Lang.JA: "DeepSeek Harness", Lang.DE: "DeepSeek Harness", Lang.FR: "DeepSeek Harness", Lang.WY: "DeepSeek Harness"},
    "new_chat":         {Lang.ZH: "新对话", Lang.EN: "New Chat", Lang.JA: "新規チャット", Lang.DE: "Neuer Chat", Lang.FR: "Nouveau chat", Lang.WY: "新談"},
    "settings":         {Lang.ZH: "设置", Lang.EN: "Settings", Lang.JA: "設定", Lang.DE: "Einstellungen", Lang.FR: "Paramètres", Lang.WY: "設置"},
    "send":             {Lang.ZH: "发送", Lang.EN: "Send", Lang.JA: "送信", Lang.DE: "Senden", Lang.FR: "Envoyer", Lang.WY: "發送"},
    "cancel":           {Lang.ZH: "取消", Lang.EN: "Cancel", Lang.JA: "キャンセル", Lang.DE: "Abbrechen", Lang.FR: "Annuler", Lang.WY: "取消"},
    "save":             {Lang.ZH: "保存", Lang.EN: "Save", Lang.JA: "保存", Lang.DE: "Speichern", Lang.FR: "Sauvegarder", Lang.WY: "存儲"},
    "delete":           {Lang.ZH: "删除", Lang.EN: "Delete", Lang.JA: "削除", Lang.DE: "Löschen", Lang.FR: "Supprimer", Lang.WY: "刪除"},
    "search":           {Lang.ZH: "搜索", Lang.EN: "Search", Lang.JA: "検索", Lang.DE: "Suchen", Lang.FR: "Rechercher", Lang.WY: "尋索"},
    "close":            {Lang.ZH: "关闭", Lang.EN: "Close", Lang.JA: "閉じる", Lang.DE: "Schließen", Lang.FR: "Fermer", Lang.WY: "闔"},
    "expand":           {Lang.ZH: "展开", Lang.EN: "Expand", Lang.JA: "展開", Lang.DE: "Ausklappen", Lang.FR: "Développer", Lang.WY: "展"},
    "collapse":         {Lang.ZH: "收起", Lang.EN: "Collapse", Lang.JA: "折り畳む", Lang.DE: "Einklappen", Lang.FR: "Réduire", Lang.WY: "收"},
    "language":         {Lang.ZH: "语言", Lang.EN: "Language", Lang.JA: "言語", Lang.DE: "Sprache", Lang.FR: "Langue", Lang.WY: "言語"},
    "theme":            {Lang.ZH: "主题", Lang.EN: "Theme", Lang.JA: "テーマ", Lang.DE: "Design", Lang.FR: "Thème", Lang.WY: "主題"},
    "light":            {Lang.ZH: "浅色", Lang.EN: "Light", Lang.JA: "ライト", Lang.DE: "Hell", Lang.FR: "Clair", Lang.WY: "明"},
    "dark":             {Lang.ZH: "深色", Lang.EN: "Dark", Lang.JA: "ダーク", Lang.DE: "Dunkel", Lang.FR: "Sombre", Lang.WY: "暗"},
    "copied":           {Lang.ZH: "已复制", Lang.EN: "Copied", Lang.JA: "コピーしました", Lang.DE: "Kopiert", Lang.FR: "Copié", Lang.WY: "已錄"},
    "model":            {Lang.ZH: "模型", Lang.EN: "Model", Lang.JA: "モデル", Lang.DE: "Modell", Lang.FR: "Modèle", Lang.WY: "模型"},
    "provider":         {Lang.ZH: "供应商", Lang.EN: "Provider", Lang.JA: "プロバイダ", Lang.DE: "Anbieter", Lang.FR: "Fournisseur", Lang.WY: "供應商"},
    "api_key":          {Lang.ZH: "API Key", Lang.EN: "API Key", Lang.JA: "APIキー", Lang.DE: "API-Schlüssel", Lang.FR: "Clé API", Lang.WY: "API 密鑰"},

    # 状态
    "connecting":       {Lang.ZH: "连接中…", Lang.EN: "Connecting…", Lang.JA: "接続中…", Lang.DE: "Verbinden…", Lang.FR: "Connexion…", Lang.WY: "連中…"},
    "connected":        {Lang.ZH: "已连接", Lang.EN: "Connected", Lang.JA: "接続済み", Lang.DE: "Verbunden", Lang.FR: "Connecté", Lang.WY: "已連"},
    "disconnected":     {Lang.ZH: "未连接", Lang.EN: "Disconnected", Lang.JA: "未接続", Lang.DE: "Getrennt", Lang.FR: "Déconnecté", Lang.WY: "未連"},
    "error":            {Lang.ZH: "出错", Lang.EN: "Error", Lang.JA: "エラー", Lang.DE: "Fehler", Lang.FR: "Erreur", Lang.WY: "誤"},
    "ready":            {Lang.ZH: "就绪", Lang.EN: "Ready", Lang.JA: "準備完了", Lang.DE: "Bereit", Lang.FR: "Prêt", Lang.WY: "備"},
    "thinking":         {Lang.ZH: "思考中…", Lang.EN: "Thinking…", Lang.JA: "思考中…", Lang.DE: "Denkt…", Lang.FR: "Réfléchit…", Lang.WY: "思中…"},
    "completed":        {Lang.ZH: "完成", Lang.EN: "Completed", Lang.JA: "完了", Lang.DE: "Abgeschlossen", Lang.FR: "Terminé", Lang.WY: "畢"},

    # 提示
    "start_hint":       {Lang.ZH: "启动运行时开始对话", Lang.EN: "Start the runtime to begin chatting", Lang.JA: "ランタイムを起動してチャットを開始", Lang.DE: "Starten Sie die Laufzeit zum Chatten", Lang.FR: "Démarrez le runtime pour discuter", Lang.WY: "啟運行時以始談話"},
    "no_key_hint":      {Lang.ZH: "未配置 API key，对话将返回错误", Lang.EN: "No API key configured", Lang.JA: "APIキーが設定されていません", Lang.DE: "Kein API-Schlüssel konfiguriert", Lang.FR: "Aucune clé API configurée", Lang.WY: "未設 API 密鑰"},
    "input_placeholder":{Lang.ZH: "输入消息…", Lang.EN: "Type a message…", Lang.JA: "メッセージを入力…", Lang.DE: "Nachricht eingeben…", Lang.FR: "Saisissez un message…", Lang.WY: "書入消息…"},
    "tool_call":        {Lang.ZH: "调用工具", Lang.EN: "Tool call", Lang.JA: "ツール呼び出し", Lang.DE: "Werkzeugaufruf", Lang.FR: "Appel d'outil", Lang.WY: "召器"},
    "tool_result":      {Lang.ZH: "工具返回", Lang.EN: "Tool result", Lang.JA: "ツール結果", Lang.DE: "Werkzeugergebnis", Lang.FR: "Résultat d'outil", Lang.WY: "器返"},
    "send_failed":      {Lang.ZH: "发送失败", Lang.EN: "Send failed", Lang.JA: "送信失敗", Lang.DE: "Senden fehlgeschlagen", Lang.FR: "Échec d'envoi", Lang.WY: "發送失"},
    "copy_success":     {Lang.ZH: "已复制", Lang.EN: "Copied", Lang.JA: "コピーしました", Lang.DE: "Kopiert", Lang.FR: "Copié", Lang.WY: "已錄"},
    "context_usage":    {Lang.ZH: "上下文用量", Lang.EN: "Context usage", Lang.JA: "コンテキスト使用量", Lang.DE: "Kontextnutzung", Lang.FR: "Utilisation du contexte", Lang.WY: "文脈用度"},
    "session_rename":   {Lang.ZH: "重命名", Lang.EN: "Rename", Lang.JA: "名前変更", Lang.DE: "Umbenennen", Lang.FR: "Renommer", Lang.WY: "更名"},
    "session_delete":   {Lang.ZH: "删除会话", Lang.EN: "Delete session", Lang.JA: "セッション削除", Lang.DE: "Sitzung löschen", Lang.FR: "Supprimer la session", Lang.WY: "刪會談"},
    "no_sessions":      {Lang.ZH: "暂无会话", Lang.EN: "No sessions", Lang.JA: "セッションがありません", Lang.DE: "Keine Sitzungen", Lang.FR: "Aucune session", Lang.WY: "無會談"},
    "settings_saved":   {Lang.ZH: "设置已保存，正在重启运行时", Lang.EN: "Settings saved, restarting runtime", Lang.JA: "設定を保存しました、ランタイムを再起動中", Lang.DE: "Einstellungen gespeichert, Laufzeit wird neu gestartet", Lang.FR: "Paramètres sauvegardés, redémarrage du runtime", Lang.WY: "設置已存，運行時重啟中"},
    "model_provider":   {Lang.ZH: "模型与密钥设置", Lang.EN: "Model & Key Settings", Lang.JA: "モデルとキー設定", Lang.DE: "Modell- und Schlüsseleinstellungen", Lang.FR: "Paramètres du modèle et de la clé", Lang.WY: "模型與密鑰設置"},
    "select_provider":  {Lang.ZH: "选择供应商", Lang.EN: "Select provider", Lang.JA: "プロバイダを選択", Lang.DE: "Anbieter auswählen", Lang.FR: "Sélectionner un fournisseur", Lang.WY: "選供應商"},
    "select_model":     {Lang.ZH: "选择模型", Lang.EN: "Select model", Lang.JA: "モデルを選択", Lang.DE: "Modell auswählen", Lang.FR: "Sélectionner un modèle", Lang.WY: "選模型"},
    "paste_key_hint":   {Lang.ZH: "粘贴 API Key…", Lang.EN: "Paste API Key…", Lang.JA: "APIキーを貼り付け…", Lang.DE: "API-Schlüssel einfügen…", Lang.FR: "Coller la clé API…", Lang.WY: "貼 API 密鑰…"},
    "show_key":         {Lang.ZH: "显示", Lang.EN: "Show", Lang.JA: "表示", Lang.DE: "Anzeigen", Lang.FR: "Afficher", Lang.WY: "示"},
    "hide_key":         {Lang.ZH: "隐藏", Lang.EN: "Hide", Lang.JA: "隠す", Lang.DE: "Verbergen", Lang.FR: "Masquer", Lang.WY: "隱"},
    "base_url":         {Lang.ZH: "Base URL", Lang.EN: "Base URL", Lang.JA: "ベースURL", Lang.DE: "Basis-URL", Lang.FR: "URL de base", Lang.WY: "基址 URL"},
    "start_runtime":    {Lang.ZH: "启动", Lang.EN: "Start", Lang.JA: "起動", Lang.DE: "Starten", Lang.FR: "Démarrer", Lang.WY: "啟"},
    "stop_runtime":     {Lang.ZH: "停止", Lang.EN: "Stop", Lang.JA: "停止", Lang.DE: "Stoppen", Lang.FR: "Arrêter", Lang.WY: "止"},

    # 主窗口
    "not_connected":    {Lang.ZH: "尚未连接运行时", Lang.EN: "Runtime not connected", Lang.JA: "ランタイム未接続", Lang.DE: "Laufzeit nicht verbunden", Lang.FR: "Runtime non connecté", Lang.WY: "尚未連接運行時"},
    "export_md":        {Lang.ZH: "导出当前对话为 Markdown", Lang.EN: "Export conversation as Markdown", Lang.JA: "会話を Markdown でエクスポート", Lang.DE: "Gespräch als Markdown exportieren", Lang.FR: "Exporter la conversation en Markdown", Lang.WY: "導出當前對話為 Markdown"},
    "attach_file":      {Lang.ZH: "附加文本文件内容", Lang.EN: "Attach text file content", Lang.JA: "テキストファイルを添付", Lang.DE: "Textdatei anhängen", Lang.FR: "Joindre un fichier texte", Lang.WY: "附加文本文件內容"},
    "enter_hint":       {Lang.ZH: "按 Enter 发送 · Shift+Enter 换行", Lang.EN: "Enter to send · Shift+Enter for newline", Lang.JA: "Enter で送信 · Shift+Enter で改行", Lang.DE: "Enter zum Senden · Shift+Enter für neue Zeile", Lang.FR: "Entrée pour envoyer · Maj+Entrée pour nouvelle ligne", Lang.WY: "按 Enter 發送 · Shift+Enter 換行"},
    "assistant_thinking":{Lang.ZH: "助手思考中…", Lang.EN: "Assistant thinking…", Lang.JA: "アシスタント思考中…", Lang.DE: "Assistent denkt…", Lang.FR: "L'assistant réfléchit…", Lang.WY: "助手思維中…"},
    "starting_runtime": {Lang.ZH: "正在启动运行时…", Lang.EN: "Starting runtime…", Lang.JA: "ランタイムを起動中…", Lang.DE: "Laufzeit wird gestartet…", Lang.FR: "Démarrage du runtime…", Lang.WY: "正在啟動運行時…"},
    "runtime_ready":    {Lang.ZH: "运行就绪 · {provider} · {model}", Lang.EN: "Runtime ready · {provider} · {model}", Lang.JA: "ランタイム準備完了 · {provider} · {model}", Lang.DE: "Laufzeit bereit · {provider} · {model}", Lang.FR: "Runtime prêt · {provider} · {model}", Lang.WY: "運行時就緒 · {provider} · {model}"},
    "runtime_not_ready":{Lang.ZH: "运行时未就绪，请稍候或在设置中配置后重试。", Lang.EN: "Runtime not ready. Wait a moment or configure it in Settings.", Lang.JA: "ランタイムが未準備です。少々お待ちいただくか、設定で構成してください。", Lang.DE: "Laufzeit nicht bereit. Warten Sie oder konfigurieren Sie sie in den Einstellungen.", Lang.FR: "Runtime non prêt. Patientez ou configurez-le dans les paramètres.", Lang.WY: "運行時未就緒，請稍候或在設置中配置後重試。"},
    "no_api_key_hint":  {Lang.ZH: "提示：未配置 {provider} 的 API Key，暂无法对话", Lang.EN: "No API key configured for {provider}; chatting unavailable", Lang.JA: "{provider} の API キーが未設定のため、チャットできません", Lang.DE: "Kein API-Schlüssel für {provider}; Chatten nicht möglich", Lang.FR: "Aucune clé API pour {provider} ; discussion indisponible", Lang.WY: "提示：未配置 {provider} 之 API 密鑰，暫無法對話"},
    "session_status":   {Lang.ZH: "会话状态：{status}", Lang.EN: "Session status: {status}", Lang.JA: "セッション状態：{status}", Lang.DE: "Sitzungsstatus: {status}", Lang.FR: "État de session : {status}", Lang.WY: "會話狀態：{status}"},
    "tool_invoke":      {Lang.ZH: "调用工具", Lang.EN: "Tool call", Lang.JA: "ツール呼び出し", Lang.DE: "Werkzeugaufruf", Lang.FR: "Appel d'outil", Lang.WY: "召器"},
    "confirm_delete_title": {Lang.ZH: "确认删除", Lang.EN: "Confirm deletion", Lang.JA: "削除の確認", Lang.DE: "Löschen bestätigen", Lang.FR: "Confirmer la suppression", Lang.WY: "確認刪除"},
    "confirm_delete_msg": {Lang.ZH: "确定要删除此对话？此操作不可恢复。", Lang.EN: "Delete this conversation? This cannot be undone.", Lang.JA: "この会話を削除しますか？この操作は元に戻せません。", Lang.DE: "Dieses Gespräch löschen? Dies kann nicht rückgängig gemacht werden.", Lang.FR: "Supprimer cette conversation ? Cette action est irréversible.", Lang.WY: "確定要刪除此對話？此操作不可恢復。"},
    "rename_title":     {Lang.ZH: "重命名对话", Lang.EN: "Rename conversation", Lang.JA: "会話名を変更", Lang.DE: "Gespräch umbenennen", Lang.FR: "Renommer la conversation", Lang.WY: "更名對話"},
    "new_name":         {Lang.ZH: "新名称：", Lang.EN: "New name:", Lang.JA: "新しい名前：", Lang.DE: "Neuer Name:", Lang.FR: "Nouveau nom :", Lang.WY: "新名稱："},
    "reasoning_applied":{Lang.ZH: "推理强度：{effort} · 已生效", Lang.EN: "Reasoning level: {effort} · applied", Lang.JA: "推理強度：{effort} · 有効", Lang.DE: "Denkaufwand: {effort} · angewendet", Lang.FR: "Niveau de raisonnement : {effort} · appliqué", Lang.WY: "推理強度：{effort} · 已生效"},
    "reasoning_pending":{Lang.ZH: "推理强度：{effort} · 重启后生效", Lang.EN: "Reasoning level: {effort} · after restart", Lang.JA: "推理強度：{effort} · 再起動後に有効", Lang.DE: "Denkaufwand: {effort} · nach Neustart", Lang.FR: "Niveau de raisonnement : {effort} · après redémarrage", Lang.WY: "推理強度：{effort} · 重啟後生效"},
    "read_file_failed": {Lang.ZH: "读取文件失败：{err}", Lang.EN: "Failed to read file: {err}", Lang.JA: "ファイル読み込みに失敗：{err}", Lang.DE: "Datei konnte nicht gelesen werden: {err}", Lang.FR: "Échec de lecture du fichier : {err}", Lang.WY: "讀取文件失敗：{err}"},
    "file_attached":    {Lang.ZH: "已附加文件内容：{name}", Lang.EN: "Attached file content: {name}", Lang.JA: "ファイル内容を添付しました：{name}", Lang.DE: "Dateiinhalt angehängt: {name}", Lang.FR: "Contenu du fichier ajouté : {name}", Lang.WY: "已附加文件內容：{name}"},
    "no_export":        {Lang.ZH: "当前没有可导出的对话。", Lang.EN: "No conversation to export.", Lang.JA: "エクスポートできる会話がありません。", Lang.DE: "Kein Gespräch zum Exportieren vorhanden.", Lang.FR: "Aucune conversation à exporter.", Lang.WY: "當前沒有可導出的對話。"},
    "export_title":     {Lang.ZH: "导出对话", Lang.EN: "Export conversation", Lang.JA: "会話をエクスポート", Lang.DE: "Gespräch exportieren", Lang.FR: "Exporter la conversation", Lang.WY: "導出對話"},
    "export_failed":    {Lang.ZH: "导出失败：{err}", Lang.EN: "Export failed: {err}", Lang.JA: "エクスポートに失敗：{err}", Lang.DE: "Export fehlgeschlagen: {err}", Lang.FR: "Échec de l'export : {err}", Lang.WY: "導出失敗：{err}"},
    "exported_to":      {Lang.ZH: "已导出到：{name}", Lang.EN: "Exported to: {name}", Lang.JA: "エクスポート先：{name}", Lang.DE: "Exportiert nach: {name}", Lang.FR: "Exporté vers : {name}", Lang.WY: "已導出至：{name}"},
    "me":               {Lang.ZH: "我", Lang.EN: "Me", Lang.JA: "私", Lang.DE: "Ich", Lang.FR: "Moi", Lang.WY: "我"},
    "deepseek_name":    {Lang.ZH: "DeepSeek", Lang.EN: "DeepSeek", Lang.JA: "DeepSeek", Lang.DE: "DeepSeek", Lang.FR: "DeepSeek", Lang.WY: "DeepSeek"},
    "tool_msg":         {Lang.ZH: "工具", Lang.EN: "Tool", Lang.JA: "ツール", Lang.DE: "Werkzeug", Lang.FR: "Outil", Lang.WY: "器"},
    "tool_running":     {Lang.ZH: "运行中", Lang.EN: "Running", Lang.JA: "実行中", Lang.DE: "Läuft", Lang.FR: "En cours", Lang.WY: "行中"},
    "tool_done":        {Lang.ZH: "已完成", Lang.EN: "Done", Lang.JA: "完了", Lang.DE: "Fertig", Lang.FR: "Terminé", Lang.WY: "已成"},
    "tool_failed":      {Lang.ZH: "出错", Lang.EN: "Failed", Lang.JA: "失敗", Lang.DE: "Fehlgeschlagen", Lang.FR: "Échec", Lang.WY: "誤"},
    "tool_args":        {Lang.ZH: "参数", Lang.EN: "Arguments", Lang.JA: "引数", Lang.DE: "Argumente", Lang.FR: "Arguments", Lang.WY: "參數"},
    "tool_output":      {Lang.ZH: "输出", Lang.EN: "Output", Lang.JA: "出力", Lang.DE: "Ausgabe", Lang.FR: "Sortie", Lang.WY: "出"},

    # 空状态
    "empty_greet":      {Lang.ZH: "今天想聊点什么？", Lang.EN: "What shall we talk about today?", Lang.JA: "今日は何を話しましょうか？", Lang.DE: "Worüber möchten Sie heute sprechen?", Lang.FR: "De quoi voulez-vous parler aujourd'hui ?", Lang.WY: "今日欲談何乎？"},
    "greet_morning":    {Lang.ZH: "早上好", Lang.EN: "Good morning", Lang.JA: "おはようございます", Lang.DE: "Guten Morgen", Lang.FR: "Bonjour", Lang.WY: "晨安"},
    "greet_noon":       {Lang.ZH: "中午好", Lang.EN: "Good noon", Lang.JA: "こんにちは", Lang.DE: "Guten Tag", Lang.FR: "Bonjour", Lang.WY: "午安"},
    "greet_afternoon":  {Lang.ZH: "下午好", Lang.EN: "Good afternoon", Lang.JA: "こんにちは", Lang.DE: "Guten Nachmittag", Lang.FR: "Bon après-midi", Lang.WY: "午安"},
    "greet_evening":    {Lang.ZH: "晚上好", Lang.EN: "Good evening", Lang.JA: "こんばんは", Lang.DE: "Guten Abend", Lang.FR: "Bonsoir", Lang.WY: "晚安"},
    "greet_dawn":       {Lang.ZH: "凌晨好", Lang.EN: "Good night", Lang.JA: "おそようございます", Lang.DE: "Gute Nacht", Lang.FR: "Bonne nuit", Lang.WY: "夜安"},
    "empty_sub":        {Lang.ZH: "从一个问题、一段文字或一份文档开始", Lang.EN: "Start with a question, a paragraph, or a document", Lang.JA: "質問、文章、またはドキュメントから始めます", Lang.DE: "Beginnen Sie mit einer Frage, einem Text oder einem Dokument", Lang.FR: "Commencez par une question, un texte ou un document", Lang.WY: "自一問、一段文字或一文檔始"},
    "sug_write_t":      {Lang.ZH: "写作与润色", Lang.EN: "Writing & Polish", Lang.JA: "文章の作成と推敲", Lang.DE: "Schreiben & Feinschliff", Lang.FR: "Rédaction & polyshing", Lang.WY: "寫作與潤色"},
    "sug_write_d":      {Lang.ZH: "起草文案、改写语气、调整结构", Lang.EN: "Draft copy, rewrite tone, adjust structure", Lang.JA: "文案の起草、トーン調整、構成整理", Lang.DE: "Entwürfe, Tonfall anpassen, Struktur ordnen", Lang.FR: "Rédiger, ajuster le ton, structurer", Lang.WY: "起草文案、改寫語氣、調整結構"},
    "sug_write_p":      {Lang.ZH: "帮我写一份产品发布公告的初稿，语气正式但不生硬，结尾带上行动号召。", Lang.EN: "Help me draft a product launch announcement, formal but not stiff, with a call to action.", Lang.JA: "製品発表のお知らせの初稿を書いてください。固すぎずフォーマルな口調で、最後に行動喚起を添えて。", Lang.DE: "Schreiben Sie einen Entwurf einer Produkteinführungs-Ankündigung, formell aber nicht steif, mit einem Aufruf zum Handeln.", Lang.FR: "Rédigez un brouillon d'annonce de lancement de produit, formel mais pas rigide, avec un appel à l'action.", Lang.WY: "為我起草一份產品發佈公告初稿，語氣正式而不生硬，結尾附行動號召。"},
    "sug_code_t":       {Lang.ZH: "代码理解与调试", Lang.EN: "Code Understanding & Debugging", Lang.JA: "コード理解とデバッグ", Lang.DE: "Code verstehen & debuggen", Lang.FR: "Compréhension et débogage de code", Lang.WY: "代碼理解與調試"},
    "sug_code_d":       {Lang.ZH: "读懂逻辑、定位 Bug、给出修复", Lang.EN: "Understand logic, locate bugs, propose fixes", Lang.JA: "ロジック把握・バグ特定・修正提案", Lang.DE: "Logik verstehen, Fehler finden, Fixes vorschlagen", Lang.FR: "Comprendre la logique, localiser les bugs, proposer des correctifs", Lang.WY: "讀懂邏輯、定位 Bug、給出修復"},
    "sug_code_p":       {Lang.ZH: "解释一下下面这段代码在做什么，并指出可以优化的地方：", Lang.EN: "Explain what this code does and point out where it can be improved:", Lang.JA: "このコードが何をするか説明し、改善点を指摘してください：", Lang.DE: "Erkläre, was dieser Code tut, und nenne Verbesserungsmöglichkeiten:", Lang.FR: "Expliquez ce que fait ce code et indiquez comment l'améliorer :", Lang.WY: "解釋以下這段代碼在做什麼，並指出可優化之處："},
    "sug_trans_t":      {Lang.ZH: "翻译与跨语言", Lang.EN: "Translation & Languages", Lang.JA: "翻訳と言語", Lang.DE: "Übersetzung & Sprachen", Lang.FR: "Traduction et langues", Lang.WY: "翻譯與跨語言"},
    "sug_trans_d":      {Lang.ZH: "中英互译、术语统一、母语润色", Lang.EN: "Translate, unify terms, polish as a native", Lang.JA: "中英翻訳・用語統一・母語レベルの推敲", Lang.DE: "Übersetzen, Terminologie vereinheitlichen, muttersprachlich feilen", Lang.FR: "Traduire, unifier la terminologie, peaufiner comme un natif", Lang.WY: "中英互譯、術語統一、母語潤色"},
    "sug_trans_p":      {Lang.ZH: "把下面这段话翻译成英文，保持语气自然、接近母语表达：", Lang.EN: "Translate the following into English, keeping the tone natural and native-like:", Lang.JA: "次の文章を英語に翻訳し、自然で母語らしい表現にしてください：", Lang.DE: "Übersetze das Folgende ins Englische, natürlich und muttersprachlich:", Lang.FR: "Traduisez ce qui suit en anglais, de façon naturelle et idiomatique :", Lang.WY: "將以下這段話譯為英文，保持語氣自然、接近母語表達："},
    "sug_sum_t":        {Lang.ZH: "总结与提炼", Lang.EN: "Summarize & Distill", Lang.JA: "要約と抽出", Lang.DE: "Zusammenfassen & destillieren", Lang.FR: "Résumé et synthèse", Lang.WY: "總結與提煉"},
    "sug_sum_d":        {Lang.ZH: "长文提炼、要点归纳、结论先行", Lang.EN: "Distill long text, list key points, conclusion first", Lang.JA: "長文の要点抽出・整理・結論先行", Lang.DE: "Lange Texte destillieren, Kernthesen listen, Fazit zuerst", Lang.FR: "Distiller les textes longs, lister les points clés, conclusion d'abord", Lang.WY: "長文提煉、要點歸納、結論先行"},
    "sug_sum_p":        {Lang.ZH: "总结这篇文章的要点，用结构化列表输出，并给出关键结论。", Lang.EN: "Summarize this article's key points in a structured list, with a key conclusion.", Lang.JA: "この記事の要点を構造化リストでまとめ、重要な結論を示してください。", Lang.DE: "Fasse die Kernpunkte dieses Artikels in einer strukturierten Liste zusammen, mit einer Schlussfolgerung.", Lang.FR: "Résumez les points clés de cet article en liste structurée, avec une conclusion clé.", Lang.WY: "總結此文要點，以結構化列表輸出，並給出關鍵結論。"},

    # 思考块
    "thinking_done":    {Lang.ZH: "已深度思考", Lang.EN: "Deep thinking done", Lang.JA: "深く考えました", Lang.DE: "Tiefes Denken abgeschlossen", Lang.FR: "Réflexion approfondie terminée", Lang.WY: "已深度思考"},
    "thinking_running": {Lang.ZH: "深度思考中", Lang.EN: "Thinking deeply…", Lang.JA: "深く思考中…", Lang.DE: "Denkt tief nach…", Lang.FR: "Réflexion approfondie en cours…", Lang.WY: "深度思考中"},

    # 侧边栏分组
    "group_today":      {Lang.ZH: "今天", Lang.EN: "Today", Lang.JA: "今日", Lang.DE: "Heute", Lang.FR: "Aujourd'hui", Lang.WY: "今日"},
    "group_earlier":    {Lang.ZH: "更早", Lang.EN: "Earlier", Lang.JA: "以前", Lang.DE: "Früher", Lang.FR: "Plus tôt", Lang.WY: "更早"},

    # 设置对话框
    "settings_title":   {Lang.ZH: "模型与密钥设置", Lang.EN: "Model & Key Settings", Lang.JA: "モデルとキー設定", Lang.DE: "Modell- und Schlüsseleinstellungen", Lang.FR: "Paramètres du modèle et de la clé", Lang.WY: "模型與密鑰設置"},
    "provider_label":   {Lang.ZH: "模型供应商", Lang.EN: "Provider", Lang.JA: "プロバイダ", Lang.DE: "Anbieter", Lang.FR: "Fournisseur", Lang.WY: "模型供應商"},
    "reasoning_label":  {Lang.ZH: "思考强度", Lang.EN: "Reasoning level", Lang.JA: "思考強度", Lang.DE: "Denkaufwand", Lang.FR: "Niveau de raisonnement", Lang.WY: "思考強度"},
    "base_url_label":   {Lang.ZH: "Base URL (自定义端点)", Lang.EN: "Base URL (custom endpoint)", Lang.JA: "Base URL（カスタムエンドポイント）", Lang.DE: "Basis-URL (benutzerdefinierter Endpunkt)", Lang.FR: "URL de base (point d'accès personnalisé)", Lang.WY: "Base URL（自定義端點）"},
    "paste_key_hint":   {Lang.ZH: "粘贴 API Key…", Lang.EN: "Paste API Key…", Lang.JA: "APIキーを貼り付け…", Lang.DE: "API-Schlüssel einfügen…", Lang.FR: "Coller la clé API…", Lang.WY: "貼上 API 密鑰…"},
    "save_restart":     {Lang.ZH: "保存并重启", Lang.EN: "Save & Restart", Lang.JA: "保存して再起動", Lang.DE: "Speichern & Neustart", Lang.FR: "Enregistrer et redémarrer", Lang.WY: "存儲並重啟"},
    "key_injected_hint":{Lang.ZH: "密钥通过 {env} 环境变量注入，供运行时读取。", Lang.EN: "The key is injected via the {env} environment variable for the runtime.", Lang.JA: "{env} 環境変数でキーを注入し、ランタイムが読み取ります。", Lang.DE: "Der Schlüssel wird über die Umgebungsvariable {env} für die Laufzeit injiziert.", Lang.FR: "La clé est injectée via la variable d'environnement {env} pour le runtime.", Lang.WY: "密鑰通過 {env} 環境變數注入，供運行時讀取。"},
    "settings_tip":     {Lang.ZH: "配置与网页端共用同一后端（~/.dsh）。切换供应商后自动采用新模型档位。", Lang.EN: "Configuration shares the same backend as the web end (~/.dsh). Switching providers applies the new model levels automatically.", Lang.JA: "設定はウェブ版と同じバックエンド（~/.dsh）を共有します。プロバイダを切り替えると新しいモデル段階が自動適用されます。", Lang.DE: "Die Konfiguration teilt dasselbe Backend wie das Web-Interface (~/.dsh). Beim Wechsel des Anbieters werden die neuen Modellstufen automatisch übernommen.", Lang.FR: "La configuration partage le même backend que la version web (~/.dsh). Le changement de fournisseur applique automatiquement les nouveaux niveaux de modèle.", Lang.WY: "配置與網頁端共用同一後端（~/.dsh）。切換供應商後自動採用新模型檔位。"},
    "settings_saved":   {Lang.ZH: "设置已保存，正在按新配置重启运行时…", Lang.EN: "Settings saved, restarting the runtime…", Lang.JA: "設定を保存しました。ランタイムを再起動しています…", Lang.DE: "Einstellungen gespeichert, Laufzeit wird neu gestartet…", Lang.FR: "Paramètres enregistrés, redémarrage du runtime…", Lang.WY: "設置已存儲，正在按新配置重啟運行時…"},
    "checking_deps":    {Lang.ZH: "检查依赖…", Lang.EN: "Checking dependencies…", Lang.JA: "依存を確認中…", Lang.DE: "Prüfe Abhängigkeiten…", Lang.FR: "Vérification des dépendances…", Lang.WY: "檢查依賴…"},
    "waiting_handshake":{Lang.ZH: "等待握手…", Lang.EN: "Waiting for handshake…", Lang.JA: "ハンドシェイク待機中…", Lang.DE: "Warte auf Handshake…", Lang.FR: "Attente du handshake…", Lang.WY: "等待握手…"},
    "stopped":          {Lang.ZH: "已停止", Lang.EN: "Stopped", Lang.JA: "停止済み", Lang.DE: "Gestoppt", Lang.FR: "Arrêté", Lang.WY: "已停"},

    # harness 模式（agent preset）
    "harness_mode":     {Lang.ZH: "Harness 模式", Lang.EN: "Harness mode", Lang.JA: "Harness モード", Lang.DE: "Harness-Modus", Lang.FR: "Mode Harness", Lang.WY: "Harness 模式"},

    # 工作区
    "workspace":        {Lang.ZH: "工作区", Lang.EN: "Workspace", Lang.JA: "ワークスペース", Lang.DE: "Arbeitsbereich", Lang.FR: "Espace de travail", Lang.WY: "工作區"},
    "add_workspace":    {Lang.ZH: "添加…", Lang.EN: "Add…", Lang.JA: "追加…", Lang.DE: "Hinzufügen…", Lang.FR: "Ajouter…", Lang.WY: "添加…"},
    "workspace_title":  {Lang.ZH: "工作区标题", Lang.EN: "Workspace title", Lang.JA: "ワークスペース名", Lang.DE: "Arbeitsbereich-Titel", Lang.FR: "Titre de l'espace de travail", Lang.WY: "工作區標題"},
    "workspace_invalid":{Lang.ZH: "所选目录无效或不存在。", Lang.EN: "The selected directory is invalid or does not exist.", Lang.JA: "選択したディレクトリは無効または存在しません。", Lang.DE: "Das ausgewählte Verzeichnis ist ungültig oder existiert nicht.", Lang.FR: "Le dossier sélectionné est invalide ou n'existe pas.", Lang.WY: "所選目錄無效或不存在。"},
}

_current_lang = Lang.ZH
_lang_listeners: list[callable] = []

def on_lang_change(cb: callable):
    """注册语言切换回调，每次语言改变时被调用。"""
    _lang_listeners.append(cb)

def set_lang(lang: Lang):
    global _current_lang
    _current_lang = lang
    for cb in _lang_listeners:
        try:
            cb(lang)
        except BaseException:
            pass

def get_lang() -> Lang:
    return _current_lang

def tr(key: str) -> str:
    """翻译 key 到当前语言。"""
    entry = _T.get(key)
    if entry is None:
        return key
    return entry.get(_current_lang, entry.get(Lang.ZH, key))