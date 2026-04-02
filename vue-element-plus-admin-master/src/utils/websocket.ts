import { ref, reactive, onUnmounted } from 'vue'

export interface WsStatus {
  frontend_count: number
  gui_count: number
  frontend_clients: Array<{
    client_id: string
    last_heartbeat: string
  }>
  gui_clients: Array<{
    client_id: string
    last_heartbeat: string
  }>
}

export interface WsMessage {
  type: string
  data?: WsStatus
  client_type?: string
  client_id?: string
  message?: string
  timestamp?: string
  from_type?: string
  from_id?: string
}

class WebSocketService {
  private ws: WebSocket | null = null
  private clientId: string
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private initialReconnectDelay = 3000
  private maxReconnectDelay = 30000
  private heartbeatInterval = 30000
  private connectionTimeout: number | null = null
  private connectionTimeoutMs = 10000
  
  public connected = ref(false)
  public status = reactive<WsStatus>({
    frontend_count: 0,
    gui_count: 0,
    frontend_clients: [],
    gui_clients: []
  })
  public lastMessage = ref<WsMessage | null>(null)
  public onMessageCallback: ((message: WsMessage) => void) | null = null

  constructor() {
    this.clientId = `frontend_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }
  
  private getReconnectDelay(): number {
    const delay = this.initialReconnectDelay * Math.pow(2, this.reconnectAttempts)
    return Math.min(delay, this.maxReconnectDelay)
  }

  connect(url: string = '') {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const baseUrl = url || `${protocol}//${window.location.host}`
    const wsUrl = `${baseUrl}/ws/status/frontend/${this.clientId}`
    
    try {
      console.log(`[WebSocket] 正在连接: ${wsUrl}`)
      this.ws = new WebSocket(wsUrl)
      
      this.connectionTimeout = window.setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.error('[WebSocket] 连接超时')
          this.ws.close()
        }
      }, this.connectionTimeoutMs)
      
      this.ws.onopen = () => {
        console.log('[WebSocket] 已连接')
        this.connected.value = true
        this.reconnectAttempts = 0
        this.clearConnectionTimeout()
        this.startHeartbeat()
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message: WsMessage = JSON.parse(event.data)
          this.lastMessage.value = message
          
          if (message.type === 'status_update' && message.data) {
            Object.assign(this.status, message.data)
          }
          
          if (message.type === 'client_joined' || message.type === 'client_left') {
            if (message.status) {
              Object.assign(this.status, message.status)
            }
          }
          
          if (this.onMessageCallback) {
            this.onMessageCallback(message)
          }
        } catch (e) {
          console.error('[WebSocket] 解析消息失败:', e)
        }
      }
      
      this.ws.onclose = (event) => {
        console.log('[WebSocket] 连接关闭:', event.code, event.reason)
        this.connected.value = false
        this.stopHeartbeat()
        this.clearConnectionTimeout()
        this.scheduleReconnect(url)
      }
      
      this.ws.onerror = (error) => {
        console.error('[WebSocket] 连接错误:', error)
        this.connected.value = false
        this.clearConnectionTimeout()
      }
    } catch (error) {
      console.error('[WebSocket] 创建连接失败:', error)
      this.scheduleReconnect(url)
    }
  }
  
  private clearConnectionTimeout() {
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout)
      this.connectionTimeout = null
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'heartbeat',
          timestamp: new Date().toISOString()
        }))
      }
    }, this.heartbeatInterval)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private scheduleReconnect(url: string) {
    if (this.reconnectTimer) {
      return
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.getReconnectDelay()
      console.log(`[WebSocket] 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})，延迟 ${delay}ms...`)
      
      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null
        this.connect(url)
      }, delay)
    } else {
      console.log('[WebSocket] 达到最大重连次数，将在60秒后重试')
      this.reconnectAttempts = 0
      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null
        this.connect(url)
      }, this.maxReconnectDelay * 2)
    }
  }

  disconnect() {
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connected.value = false
  }

  send(message: object) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  getStatus() {
    this.send({ type: 'get_status' })
  }

  onMessage(callback: (message: WsMessage) => void) {
    this.onMessageCallback = callback
  }
}

const wsService = new WebSocketService()

export function useWebSocket() {
  return {
    connect: (url?: string) => wsService.connect(url),
    disconnect: () => wsService.disconnect(),
    send: (message: object) => wsService.send(message),
    getStatus: () => wsService.getStatus(),
    onMessage: (callback: (message: WsMessage) => void) => wsService.onMessage(callback),
    connected: wsService.connected,
    status: wsService.status,
    lastMessage: wsService.lastMessage
  }
}

export function useWebSocketStatus() {
  const { connected, status } = useWebSocket()
  
  const frontendOnline = computed(() => status.frontend_count)
  const guiOnline = computed(() => status.gui_count)
  const totalOnline = computed(() => status.frontend_count + status.gui_count)
  
  return {
    connected,
    status,
    frontendOnline,
    guiOnline,
    totalOnline
  }
}

export default wsService
