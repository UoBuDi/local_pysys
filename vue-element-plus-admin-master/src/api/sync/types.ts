export interface DatabaseConfig {
  host: string
  port: number
  user: string
  password: string
  database: string
  charset: string
}

export interface SyncConfig {
  REMOTE_DB: DatabaseConfig
  LOCAL_DB: DatabaseConfig
  SYNC: {
    batch_size: string
    retry_count: string
    timeout: string
  }
}

export interface TestConnectionRequest {
  host: string
  port: number
  user: string
  password: string
  database: string
  charset: string
}

export interface StartSyncRequest {
  months: string[]
}

export interface SyncStatusResponse {
  is_running: boolean
  progress: number
  message: string
}

export interface LogResponse {
  content: string
  timestamp: string
}
