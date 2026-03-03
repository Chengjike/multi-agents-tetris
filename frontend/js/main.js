/**
 * 主程序
 */
(function() {
    // 配置
    const WS_URL = `ws://${window.location.host || 'localhost:8765'}/ws`;

    // DOM 元素
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const restartBtn = document.getElementById('restartBtn');
    const gameStatus = document.getElementById('gameStatus');
    const gameOverModal = document.getElementById('gameOverModal');
    const winnerSpan = document.getElementById('winner');
    const finalScoresList = document.getElementById('finalScores');

    // 游戏组件
    let ws = null;
    let renderer = null;
    let canvases = [];
    let scoreElements = [];
    let statusElements = [];
    let bgMusic = null;
    let isMusicPlaying = false;

    // 初始化背景音乐（使用 Web Audio API 合成，无需外部文件）
    function initMusic() {
        if (!window.AudioContext && !window.webkitAudioContext) return;
        
        window.bgAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
        let isPlaying = false;
        
        // 简单的俄罗斯方块风格音乐
        const melody = [
            { note: 220, duration: 0.2 },  // A3
            { note: 0, duration: 0.1 },    // pause
            { note: 262, duration: 0.2 },  // C4
            { note: 0, duration: 0.1 },
            { note: 294, duration: 0.2 },  // D4
            { note: 0, duration: 0.1 },
            { note: 262, duration: 0.2 },  // C4
            { note: 0, duration: 0.1 },
            { note: 220, duration: 0.2 },  // A3
            { note: 0, duration: 0.1 },
            { note: 196, duration: 0.4 },  // G3
            { note: 0, duration: 0.3 },
            { note: 220, duration: 0.2 },  // A3
            { note: 0, duration: 0.1 },
            { note: 262, duration: 0.2 },  // C4
            { note: 0, duration: 0.1 },
            { note: 294, duration: 0.2 },  // D4
            { note: 0, duration: 0.1 },
            { note: 330, duration: 0.4 },  // E4
            { note: 0, duration: 0.3 },
            { note: 294, duration: 0.2 },  // D4
            { note: 0, duration: 0.1 },
            { note: 262, duration: 0.2 },  // C4
            { note: 0, duration: 0.1 },
            { note: 220, duration: 0.2 },  // A3
            { note: 0, duration: 0.1 },
            { note: 196, duration: 0.4 },  // G3
            { note: 0, duration: 0.5 },
        ];

        function playNote(frequency, duration, startTime) {
            if (frequency === 0) return;

            const oscillator = window.bgAudioCtx.createOscillator();
            const gainNode = window.bgAudioCtx.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(window.bgAudioCtx.destination);

            oscillator.type = 'sine';
            oscillator.frequency.value = frequency;

            gainNode.gain.setValueAtTime(0.15, startTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);

            oscillator.start(startTime);
            oscillator.stop(startTime + duration);
        }

        function playMelody() {
            if (!isPlaying) return;

            let startTime = window.bgAudioCtx.currentTime;
            melody.forEach(({ note, duration }) => {
                playNote(note, duration, startTime);
                startTime += duration;
            });

            setTimeout(playMelody, (startTime - window.bgAudioCtx.currentTime) * 1000);
        }

        // 创建一个可控制的音乐对象
        bgMusic = {
            play: function() {
                if (window.bgAudioCtx.state === 'suspended') {
                    window.bgAudioCtx.resume();
                }
                isPlaying = true;
                playMelody();
            },
            pause: function() {
                isPlaying = false;
            },
            stop: function() {
                isPlaying = false;
            }
        };
    }

    function playMusic() {
        if (bgMusic && !isMusicPlaying) {
            try {
                bgMusic.play();
                isMusicPlaying = true;
            } catch (e) {
                console.log('播放音乐失败:', e);
            }
        }
    }

    function stopMusic() {
        if (bgMusic && isMusicPlaying) {
            try {
                if (bgMusic.pause) {
                    bgMusic.pause();
                } else {
                    bgMusic.stop();
                }
                isMusicPlaying = false;
            } catch (e) {
                console.log('停止音乐失败:', e);
            }
        }
    }

    // 初始化
    function init() {
        // 初始化背景音乐
        initMusic();
        
        // 创建渲染器
        renderer = new GameRenderer();

        // 获取画布
        document.querySelectorAll('.board').forEach(canvas => {
            canvases[parseInt(canvas.dataset.player)] = canvas;
        });

        // 获取分数和状态元素
        document.querySelectorAll('.player').forEach((el, index) => {
            scoreElements[index] = el.querySelector('.score');
            statusElements[index] = el.querySelector('.status-text');
        });

        // 创建 WebSocket 连接
        ws = new TetrisWebSocket(WS_URL);

        // 设置事件处理
        ws.on('onConnect', onConnect);
        ws.on('onDisconnect', onDisconnect);
        ws.on('onGameState', onGameState);
        ws.on('onGameOver', onGameOver);
        ws.on('onError', onError);

        // 绑定按钮事件
        startBtn.addEventListener('click', () => {
            playMusic();  // 用户点击后播放音乐
            ws.startGame();
        });
        stopBtn.addEventListener('click', () => {
            // 停止游戏
            stopBtn.disabled = true;
            startBtn.disabled = false;
            gameStatus.textContent = '已停止';
            stopMusic();  // 停止音乐
        });
        restartBtn.addEventListener('click', () => {
            gameOverModal.classList.add('hidden');
            playMusic();  // 重新开始播放音乐
            ws.startGame();
        });

        // 尝试连接
        connect();
    }

    async function connect() {
        try {
            await ws.connect();
            console.log('Connected to server');
        } catch (e) {
            console.error('Failed to connect:', e);
            setTimeout(connect, 3000); // 3秒后重试
        }
    }

    function onConnect() {
        updateConnectionStatus(true);
    }

    function onDisconnect() {
        updateConnectionStatus(false);
        // 自动重连
        setTimeout(connect, 3000);
    }

    function updateConnectionStatus(connected) {
        let statusEl = document.querySelector('.connection-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.className = 'connection-status';
            document.body.appendChild(statusEl);
        }
        statusEl.className = 'connection-status ' + (connected ? 'connected' : 'disconnected');
        statusEl.textContent = connected ? '已连接' : '断开连接';
    }

    function onGameState(data) {
        // 更新游戏状态显示
        gameStatus.textContent = '游戏中 (Tick: ' + (data.tick || 0) + ')';

        // 启用/禁用按钮
        startBtn.disabled = true;
        stopBtn.disabled = false;

        // 渲染每个玩家
        data.players.forEach((player, index) => {
            const canvas = canvases[index];
            if (canvas) {
                renderer.render(canvas, player);
            }

            // 更新分数
            renderer.updateScore(scoreElements[index], player.score);

            // 更新状态
            const status = player.status === 'game_over' ? 'dead' : 'alive';
            renderer.updateStatus(statusElements[index], status);
        });
    }

    function onGameOver(data) {
        // 显示游戏结束弹窗
        winnerSpan.textContent = '玩家 ' + data.winner;

        // 显示最终分数
        finalScoresList.innerHTML = '';
        data.final_scores.forEach((score, index) => {
            const li = document.createElement('li');
            li.textContent = `玩家 ${index}: ${score} 分`;
            if (index === data.winner) {
                li.style.color = '#00ff88';
                li.style.fontWeight = 'bold';
            }
            finalScoresList.appendChild(li);
        });

        gameOverModal.classList.remove('hidden');

        // 更新按钮状态
        startBtn.disabled = false;
        stopBtn.disabled = true;
        gameStatus.textContent = '游戏结束';
    }

    function onError(error) {
        console.error('Game error:', error);
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();