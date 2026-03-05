/**
 * 主程序
 */
(function() {
    // DOM 元素
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const restartBtn = document.getElementById('restartBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const gameStatus = document.getElementById('gameStatus');
    const gameOverModal = document.getElementById('gameOverModal');
    const winnerSpan = document.getElementById('winner');
    const finalScoresList = document.getElementById('finalScores');
    const scoreList = document.getElementById('scoreList');

    // 游戏组件 - 使用 HTTP + SSE 客户端
    let client = null;
    let renderers = [];
    let canvases = [];
    let nextCanvases = [];
    let scoreElements = [];
    let statusElements = [];
    let bgMusic = null;
    let isMusicPlaying = false;

    // MIDI 音乐 URL
    const MUSIC_URL = 'https://bitmidi.com/uploads/100444.mid';

    // 初始化背景音乐（使用 MIDI 文件）
    function initMusic() {
        // 不在页面加载时初始化音乐，只在点击开始时初始化
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

    // 加载 MIDI 音乐
    async function loadMidiMusic() {
        try {
            const response = await fetch(MUSIC_URL);
            const arrayBuffer = await response.arrayBuffer();
            
            // 使用 Web Audio API 播放 MIDI
            window.bgAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            
            // 简化的 MIDI 播放 - 循环播放一个简单的旋律
            const melody = [
                { note: 220, duration: 0.3 },
                { note: 0, duration: 0.1 },
                { note: 262, duration: 0.3 },
                { note: 0, duration: 0.1 },
                { note: 294, duration: 0.3 },
                { note: 0, duration: 0.1 },
                { note: 262, duration: 0.3 },
                { note: 0, duration: 0.1 },
                { note: 220, duration: 0.3 },
                { note: 0, duration: 0.1 },
                { note: 196, duration: 0.5 },
                { note: 0, duration: 0.3 },
            ];

            let melodyIndex = 0;
            
            function playMelody() {
                if (!isMusicPlaying) return;
                
                const note = melody[melodyIndex];
                if (note.note > 0) {
                    const oscillator = window.bgAudioCtx.createOscillator();
                    const gainNode = window.bgAudioCtx.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(window.bgAudioCtx.destination);
                    
                    oscillator.type = 'sine';
                    oscillator.frequency.value = note.note;
                    
                    gainNode.gain.setValueAtTime(0.15, window.bgAudioCtx.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, window.bgAudioCtx.currentTime + note.duration);
                    
                    oscillator.start(window.bgAudioCtx.currentTime);
                    oscillator.stop(window.bgAudioCtx.currentTime + note.duration);
                }
                
                melodyIndex = (melodyIndex + 1) % melody.length;
                setTimeout(playMelody, note.duration * 1000);
            }
            
            bgMusic = {
                play: function() {
                    if (window.bgAudioCtx && window.bgAudioCtx.state === 'suspended') {
                        window.bgAudioCtx.resume();
                    }
                    isMusicPlaying = true;
                    playMelody();
                },
                pause: function() {
                    isMusicPlaying = false;
                },
                stop: function() {
                    isMusicPlaying = false;
                }
            };
        } catch (e) {
            console.log('加载音乐失败:', e);
        }
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

        // 为每个玩家创建独立的渲染器
        renderers = [new GameRenderer(), new GameRenderer(), new GameRenderer()];

        // 获取画布
        document.querySelectorAll('.board').forEach(canvas => {
            canvases[parseInt(canvas.dataset.player)] = canvas;
        });
        
        // 获取下一个方块画布
        document.querySelectorAll('.next-canvas').forEach(canvas => {
            nextCanvases[parseInt(canvas.dataset.player)] = canvas;
        });

        // 获取分数和状态元素
        document.querySelectorAll('.player').forEach((el, index) => {
            scoreElements[index] = el.querySelector('.score');
            statusElements[index] = el.querySelector('.status-text');
        });

        // 创建 HTTP + SSE 客户端
        client = new TetrisHTTPClient();

        // 设置事件处理
        client.on('onConnect', onConnect);
        client.on('onDisconnect', onDisconnect);
        client.on('onGameState', onGameState);
        client.on('onGameOver', onGameOver);
        client.on('onError', onError);

        // 绑定按钮事件
        startBtn.addEventListener('click', async () => {
            // 加载并播放音乐
            await loadMidiMusic();
            playMusic();
            client.startGame();
        });
        stopBtn.addEventListener('click', () => {
            // 发送停止消息到服务器
            client.stopGame();
            // 停止游戏
            stopBtn.disabled = true;
            startBtn.disabled = false;
            gameStatus.textContent = '已停止';
            stopMusic();  // 停止音乐
        });
        restartBtn.addEventListener('click', async () => {
            gameOverModal.classList.add('hidden');
            // 加载并播放音乐
            await loadMidiMusic();
            playMusic();
            client.restartGame();
        });
        
        // 关闭弹窗按钮
        closeModalBtn.addEventListener('click', () => {
            gameOverModal.classList.add('hidden');
        });

        // 尝试连接
        connect();
    }

    function connect() {
        try {
            client.connectSSE();
            console.log('Connected to server via SSE');
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

    // 追踪每个玩家的行数，用于检测消除
    const prevLinesCleared = [0, 0, 0];

    function onGameState(data) {
        console.log('onGameState called with tick:', data.tick);
        // 更新游戏状态显示
        gameStatus.textContent = '游戏中 (Tick: ' + (data.tick || 0) + ')';

        // 启用/禁用按钮
        startBtn.disabled = true;
        stopBtn.disabled = false;

        // 更新得分排行榜
        const playerNames = ['Александр', 'Михаил', 'Иван'];
        const sortedPlayers = data.players
            .map((p, i) => ({ name: playerNames[i], score: p.score, status: p.status }))
            .sort((a, b) => b.score - a.score);
        
        scoreList.innerHTML = sortedPlayers.map(p => 
            `<li><span class="player-name">${p.name}</span><span class="player-score">${p.score}</span></li>`
        ).join('');

        // 渲染每个玩家
        data.players.forEach((player, index) => {
            const renderer = renderers[index];
            console.log('Rendering player', index, 'canvas exists:', !!canvases[index], 'score element:', !!scoreElements[index]);

            // 检测是否有行消除（通过 lines_cleared 增加）
            const currentLines = player.lines_cleared || 0;
            const clearedRows = player.last_cleared_rows || [];

            if (currentLines > prevLinesCleared[index] && clearedRows.length > 0) {
                // 只闪烁消除的行（闪烁4次：亮-暗-亮-暗-亮-暗-亮-暗）
                console.log('Player', index, 'cleared rows:', clearedRows);
                renderer.setFlashLines(clearedRows);
                // 闪烁4次，每次200ms
                setTimeout(() => renderer.clearFlash(), 200);
                setTimeout(() => renderer.setFlashLines(clearedRows), 400);
                setTimeout(() => renderer.clearFlash(), 600);
                setTimeout(() => renderer.setFlashLines(clearedRows), 800);
                setTimeout(() => renderer.clearFlash(), 1000);
                setTimeout(() => renderer.setFlashLines(clearedRows), 1200);
                setTimeout(() => renderer.clearFlash(), 1400);
                // 1.5秒后清除闪烁效果
                setTimeout(() => renderer.clearFlash(), 1500);
            }
            prevLinesCleared[index] = currentLines;

            const canvas = canvases[index];
            console.log('Canvas for player', index, ':', canvas);
            if (canvas) {
                console.log('Calling renderer.render for player', index);
                renderer.render(canvas, player);
            } else {
                console.error('Canvas not found for player', index);
            }

            // 更新分数
            if (scoreElements[index]) {
                renderer.updateScore(scoreElements[index], player.score);
            }

            // 更新状态
            const status = player.status === 'game_over' ? 'dead' : 'alive';
            if (statusElements[index]) {
                renderer.updateStatus(statusElements[index], status);
            }
            
            // 渲染下一个方块
            if (player.next_piece && nextCanvases[index]) {
                renderer.renderNextPiece(nextCanvases[index], player.next_piece);
            }
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
        
        // 停止音乐
        stopMusic();
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