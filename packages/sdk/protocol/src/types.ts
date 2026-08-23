/**
 * Named wire types for the DeepSeek Harness SDK runtime protocol: the three
 * request/result pairs and the four server-to-client notification payloads
 * exchanged over the newline-delimited JSON-RPC stdio transport. The server
 * plugin (`@deepseek-ai/dsh-sdk-jsonrpc-server`) and SDK clients share these shapes;
 * `serverInfo.name` stays the wire-stable `deepseek-harness-sdk-runtime`.
 *
 * @module @deepseek-ai/dsh-sdk-protocol/types
 */

import type { ContentBlock } from '@deepseek-ai/dsh-llm'
import type { SessionEvent } from '@deepseek-ai/dsh-session'
import type { SubagentStopReason } from '@deepseek-ai/dsh-subagent'

/** Parameters for the process-wide SDK handshake. */
export interface InitializeParams {
  /** Working directory recorded on every SDK-created session's header. */
  cwd: string
  /** Provider route every SDK-created agent runs on. */
  provider: string
  /** Model name every SDK-created agent runs on (the server may mount a fallback adapter; see `HarnessSdkJsonRpcServer.initialize`). */
  model: string
  /** Optional positive output-token cap inherited by SDK-created agents and their in-process descendants. */
  maxTokens?: number
  /** Optional reasoning effort level for the model (e.g. 'off', 'low', 'medium', 'high', 'max'). */
  reasoningEffort?: string
}

/** Wire-stable server identity returned by initialization. */
export interface InitializeResult {
  /** Wire-stable server identity (`deepseek-harness-sdk-runtime`) and version. */
  serverInfo: { name: string; version: string }
}

/** One user turn on one SDK session. */
export interface SessionPromptParams {
  /** The SDK-side session id; an unknown id lazily creates the agent+session pair. */
  sessionId: string
  /** The prompt content blocks, sent verbatim as the user message. */
  contentBlocks: ContentBlock[]
  /** Optional reasoning effort override applied to this session before the prompt. */
  reasoningEffort?: string
}

/** Durable enqueue receipt for one prompt. */
export interface SessionPromptResult {
  /** Identity of the queued user message. */
  messageId: string
}

/** Parameters for the read-only model-directory query. */
export interface ModelsListParams {
  /**
   * Optional provider-route filter; callers that care about specific routes
   * (for example the selected provider of a settings dialog) pass them and the
   * server returns only those routes. Omitted means every registered route.
   */
  providers?: string[]
}

/** One model a registered route serves, as disclosed by its adapter's catalog. */
export interface ModelsListModel {
  /** Model id accepted by `GenerateOptions.model` on this route. */
  id: string
  /** Human-readable model name; falls back to the id when absent. */
  name: string
}

/** One registered provider route with its disclosed model directory. */
export interface ModelsListProvider {
  /** Provider route key accepted by `InitializeParams.provider`. */
  id: string
  /** Human-readable provider name. */
  name: string
  /** Adapter-disclosed models, in adapter-preferred order. */
  models: readonly ModelsListModel[]
}

/** Result of the model-directory query. */
export interface ModelsListResult {
  /**
   * Registered routes in adapter-registration order. A route whose model
   * catalog is not available still appears with an empty `models` list.
   */
  providers: ModelsListProvider[]
}

/** Deployment-mapped SDK outcome: `ok` for an accepted result, `error` otherwise. */
export type SdkRunStatus = 'ok' | 'error'

/** `session.event` payload: one session-log event, streamed as it is recorded. */
export interface SessionEventNotification {
  /** Session the event belongs to (every session in the runtime, not only SDK-created ones). */
  sessionId: string
  /** The full session-log event envelope. */
  event: SessionEvent
}

/** Whole-agent lifecycle state for one session. */
export interface SessionStatusNotification {
  /** Session whose live agent changed status. */
  sessionId: string
  /** The whole-agent state after the transition. */
  status: 'idle' | 'running'
}

/** `subagent.started` payload: an in-runtime child session was created. */
export interface SubagentStartedNotification {
  /** The delegating session. */
  parentSessionId: string
  /** The new child session. */
  childSessionId: string
}

/** `subagent.finished` payload: an in-process subagent run ended (remote runs are not reported). */
export interface SubagentFinishedNotification {
  /** Subagent provider name that ran the child. */
  provider: string
  /** The child agent's id (equals {@link childSessionId} for local runs). */
  agentId: string
  /** The delegating session. */
  parentSessionId: string
  /** The child session. */
  childSessionId: string
  /** Deployment-mapped run outcome. */
  status: SdkRunStatus
  /** The provider-reported stop reason. */
  stopReason: SubagentStopReason
  /** The child's selected assistant output; absent when the child produced none. */
  lastAssistantMessage?: ContentBlock[]
}

/** Server-to-client notifications by JSON-RPC method name. */
export interface HarnessSdkNotificationMap {
  'session.event': SessionEventNotification
  'session.status': SessionStatusNotification
  'subagent.started': SubagentStartedNotification
  'subagent.finished': SubagentFinishedNotification
}

/** Client-to-server request methods with their param and result shapes. */
export interface HarnessSdkRequestMap {
  'initialize': { params: InitializeParams; result: InitializeResult }
  'session/prompt': { params: SessionPromptParams; result: SessionPromptResult }
  'session/setReasoningEffort': { params: { sessionId: string; reasoningEffort: string }; result: Record<string, never> }
  'models/list': { params: ModelsListParams; result: ModelsListResult }
  'shutdown': { params: undefined; result: Record<string, never> }
}
