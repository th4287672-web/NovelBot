import { ref } from 'vue'
import { useSettingsStore } from '~/stores/settings'
import { useInvalidateAllData } from '~/composables/useAllData'

type WebSocketStatus = 'connected' | 'connecting' | 'disconnected'
type UnsubscribeFunction = () => void
type MessageHandler = (data: any) => void

const status = ref<WebSocketStatus>('disconnected')
const messageHandlers: Record<string, MessageHandler[]> = {}
let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let reconnectAttempts = 0
let isManualDisconnect = false

function onMessage(type: string, handler: MessageHandler): UnsubscribeFunction {
  if (!messageHandlers[type]) messageHandlers[type] = []
  messageHandlers[type].push(handler)
  return () => {
    const handlers = messageHandlers[type]
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }
}

function dispatchMessage(data: any) {
  const { type, payload } = data
  if (type === 'pong') { return; }

  const handlers = messageHandlers[type];
  if (handlers) {
    handlers.forEach(handler => handler(payload || data));
  }
}

function disconnect() {
  isManualDisconnect = true;
  if (reconnectTimer) clearTimeout(reconnectTimer);
  socket?.close();
}

function sendMessage(message: object): boolean {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message))
    return true
  }
  // 如果连接未打开，则不发送
  console.warn('[WebSocket] 尝试在连接未打开时发送消息，消息已被忽略。');
  return false
}

function connect() {
  if (status.value === 'connecting' || (socket && socket.readyState === WebSocket.OPEN)) {
    return;
  }
  
  const settingsStore = useSettingsStore();
  const config = useRuntimeConfig();

  if (!settingsStore.userId) {
      console.error("[WebSocket]无法连接：用户ID未设置。");
      return;
  }
  
  status.value = 'connecting'
  isManualDisconnect = false

  const wsUrl = `${config.public.wsBase}/api/ws/${settingsStore.userId}`
  console.log(`[WebSocket] 正在连接到: ${wsUrl}`)

  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    console.log('✅ [WebSocket] 连接已建立')
    status.value = 'connected'
    reconnectAttempts = 0
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      dispatchMessage(data)
    } catch (error) {
      console.error('[WebSocket] 消息解析失败:', error)
    }
  }

  socket.onclose = (event) => {
    console.warn(`[WebSocket] 连接已关闭 (${event.code})`)
    status.value = 'disconnected'
    socket = null

    if (!isManualDisconnect) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
      console.log(`[WebSocket] 将在 ${delay / 1000}秒后重连...`);
      reconnectTimer = window.setTimeout(connect, delay)
      reconnectAttempts++
    }
  }

  socket.onerror = (error) => {
    console.error('[WebSocket] 发生错误:', error)
  }
}

export function useWebSocket() {
  return {
    status,
    connect,
    disconnect,
    sendMessage, // 将 sendMessage 添加到返回值中
    onMessage
  }
}