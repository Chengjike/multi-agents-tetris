/**
 * HTTP + SSE 客户端
 * 
 * 替代 WebSocket 的 HTTP API 客户端
 * 使用 REST API 进行游戏控制，使用 SSE 进行状态推送
 */
class TetrisHTTPClient {
    constructor(baseUrl = '') {
        // 自动检测基础 URL
        this.baseUrl = baseUrl || this._getBaseUrl();
        
        // 回调函数
        this.onGameState = null;
        this.onGameOver = null;
        this.onError = null;
        this.onConnect = null;
        this.onDisconnect = null;
        
        // 内部状态
        this.eventSource = null;
        this.connected = false;
        this.reconnect = true;
        this.reconnectDelay = 1000;
        this.maxReconnectAttempts = 5;
        this.reconnectCount = 0;
    }
    
    _getBaseUrl() {
        const hostname = window.location.hostname || 'localhost';
        const port = window.location.port || (window.location.protocol === 'https:' ? 443 : 80);
        return `${window.location.protocol}//${hostname}:${port}`;
    }
    
    // ========== REST API 方法 ==========
    
    async startGame() {
        const response = await fetch(`${this.baseUrl}/api/game/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return await response.json();
    }
    
    async stopGame() {
        const response = await fetch(`${this.baseUrl}/api/game/stop`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return await response.json();
    }
    
    async getState() {
        const response = await fetch(`${this.baseUrl}/api/game/state`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return await response.json();
    }

    async restartGame() {
        const response = await fetch(`${this.baseUrl}/api/game/restart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return await response.json();
    }
    
    async getStatus() {
        const response = await fetch(`${this.baseUrl}/api/game/status`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return await response.json();
    }
    
    // ========== SSE 连接 ==========
    
    connectSSE() {
        if (this.eventSource) {
            this.disconnectSSE();
        }
        
        this.eventSource = new EventSource(`${this.baseUrl}/api/game/sse`);

        console.log('EventSource created, readyState:', this.eventSource.readyState);

        this.eventSource.onopen = () => {
            console.log('SSE connected, readyState:', this.eventSource.readyState);
            this.connected = true;
            this.reconnectCount = 0;
            if (this.onConnect) {
                this.onConnect();
            }
        };
        
        this.eventSource.onmessage = (event) => {
            console.log('onmessage triggered, data:', event.data);
            try {
                const data = JSON.parse(event.data);
                this._handleMessage(data);
            } catch (e) {
                console.error('Failed to parse SSE message:', e);
            }
        };

        // 处理 game_state 事件（后端使用 event 字段指定事件类型）
        this.eventSource.addEventListener('game_state', (event) => {
            try {
                const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
                this._handleMessage(data);
            } catch (e) {
                console.error('Failed to parse game_state event:', e);
            }
        });

        // 处理 ping 事件（心跳）
        this.eventSource.addEventListener('ping', (event) => {
            // 忽略 ping 消息，或者可以用来更新连接状态
            // console.log('Ping received');
        });
        
        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.connected = false;
            
            if (this.onError) {
                this.onError('SSE connection error');
            }
            
            // 自动重连
            if (this.reconnect && this.reconnectCount < this.maxReconnectAttempts) {
                this.reconnectCount++;
                console.log(`Reconnecting... (${this.reconnectCount}/${this.maxReconnectAttempts})`);
                setTimeout(() => this.connectSSE(), this.reconnectDelay);
            }
            
            if (this.onDisconnect) {
                this.onDisconnect();
            }
        };
    }
    
    disconnectSSE() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.connected = false;
            
            if (this.onDisconnect) {
                this.onDisconnect();
            }
        }
    }
    
    _handleMessage(data) {
        console.log('_handleMessage called with type:', data.type);
        const type = data.type;

        if (type === 'game_state') {
            console.log('Calling onGameState callback');
            if (this.onGameState) {
                this.onGameState(data);
            }
        } else if (type === 'game_over') {
            if (this.onGameOver) {
                this.onGameOver(data);
            }
        } else if (type === 'error') {
            if (this.onError) {
                this.onError(data.error || 'Unknown error');
            }
        }
        // 忽略 ping 消息
    }
    
    // ========== 便捷方法 ==========
    
    // 兼容 WebSocket API 的方法名
    start() {
        return this.startGame();
    }
    
    stop() {
        return this.stopGame();
    }
    
    connect() {
        this.connectSSE();
    }
    
    disconnect() {
        this.disconnectSSE();
    }
    
    // 兼容原来的事件绑定方式
    on(event, handler) {
        switch (event) {
            case 'onGameState':
                this.onGameState = handler;
                break;
            case 'onGameOver':
                this.onGameOver = handler;
                break;
            case 'onError':
                this.onError = handler;
                break;
            case 'onConnect':
                this.onConnect = handler;
                break;
            case 'onDisconnect':
                this.onDisconnect = handler;
                break;
        }
    }
}

// 导出
window.TetrisHTTPClient = TetrisHTTPClient;