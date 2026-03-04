/**
 * WebSocket 客户端
 */
class TetrisWebSocket {
    constructor(url = 'ws://localhost/ws') {
        this.url = url;
        this.ws = null;
        this.connected = false;
        this.handlers = {
            onGameState: [],
            onGameOver: [],
            onError: [],
            onConnect: [],
            onDisconnect: [],
        };
    }

    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    this.connected = true;
                    this._trigger('onConnect');
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this._handleMessage(data);
                    } catch (e) {
                        console.error('Failed to parse message:', e);
                    }
                };

                this.ws.onclose = () => {
                    this.connected = false;
                    this._trigger('onDisconnect');
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this._trigger('onError', [error]);
                };

            } catch (e) {
                reject(e);
            }
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    send(message) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(message));
        }
    }

    startGame() {
        this.send({ type: 'start' });
    }

    stopGame() {
        this.send({ type: 'stop' });
    }

    requestStatus() {
        this.send({ type: 'status' });
    }

    on(event, handler) {
        if (this.handlers[event]) {
            this.handlers[event].push(handler);
        }
    }

    _trigger(event, args = []) {
        if (this.handlers[event]) {
            this.handlers[event].forEach(handler => handler(...args));
        }
    }

    _handleMessage(data) {
        switch (data.type) {
            case 'game_state':
                this._trigger('onGameState', [data]);
                break;
            case 'game_over':
                this._trigger('onGameOver', [data]);
                break;
            case 'error':
                this._trigger('onError', [data.error]);
                break;
            case 'welcome':
                console.log('Connected:', data.message);
                break;
        }
    }
}

// 导出
window.TetrisWebSocket = TetrisWebSocket;