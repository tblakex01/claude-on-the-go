/**
 * Claude-onTheGo Terminal Client
 * Native WebSockets with binary frames and exponential backoff reconnection
 */

class ClaudeTerminal {
    constructor() {
        // Session persistence
        this.sessionId = null;
        this.loadSessionFromStorage();

        // WebSocket config - auto-detect localhost vs network IP
        const hostname = window.location.hostname;
        this.wsUrl = `ws://${hostname}:8000/ws`;
        console.log(`[WS] Connecting to: ${this.wsUrl}`);
        if (this.sessionId) {
            console.log(`[WS] Will attempt to reconnect to session: ${this.sessionId}`);
        }
        this.ws = null;
        this.connected = false;

        // Reconnection config
        this.reconnectBaseDelay = 1000;      // 1s base
        this.reconnectMaxDelay = 30000;       // 30s max
        this.reconnectDecay = 1.5;            // 1.5x multiplier
        this.reconnectJitter = 0.3;           // ±30% jitter
        this.currentReconnectDelay = this.reconnectBaseDelay;
        this.reconnectTimer = null;

        // Heartbeat config
        this.heartbeatInterval = 30000;       // 30s
        this.heartbeatTimer = null;

        // Terminal
        this.term = null;
        this.fitAddon = null;

        // Theme config (will be sent by server)
        this.themeConfig = null;

        // Input queue (for buffering during disconnect)
        this.inputQueue = [];
        this.maxQueueSize = 100;

        this.init();
    }

    init() {
        // Detect mobile
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        const fontSize = isMobile ? 14 : 14; // Consistent font size

        // Create terminal with mobile-optimized settings
        this.term = new Terminal({
            cursorBlink: true,
            fontSize: fontSize,
            fontFamily: 'monospace',
            theme: {
                background: '#000000',
                foreground: '#ffffff',
            },
            scrollback: 10000,
            // Mobile optimizations
            convertEol: true,
            screenReaderMode: false,
            // Use canvas renderer for better scroll performance
            // Canvas is faster and smoother for scrolling on mobile
            rendererType: 'canvas',
            allowProposedApi: true,
            smoothScrollDuration: isMobile ? 0 : 100, // Instant on mobile for better feel
            // Important: Disable local echo - server handles all echo
            disableStdin: false,
            windowOptions: {},
            // Scroll optimization
            fastScrollModifier: 'alt',
            fastScrollSensitivity: 5,
        });

        // Add fit addon for responsive sizing
        this.fitAddon = new FitAddon.FitAddon();
        this.term.loadAddon(this.fitAddon);

        // Add web links addon
        const webLinksAddon = new WebLinksAddon.WebLinksAddon();
        this.term.loadAddon(webLinksAddon);

        // Open terminal in container
        const container = document.getElementById('terminal-container');
        this.term.open(container);

        // Initial fit with proper delay to ensure DOM is ready
        // Mobile needs more time for accurate measurements
        const fitDelay = isMobile ? 300 : 100;
        setTimeout(() => {
            console.log('[INIT] Initial terminal fit...');
            this.fitAddon.fit();
            console.log(`[INIT] Terminal sized to ${this.term.rows}x${this.term.cols}`);

            // Connect WebSocket AFTER terminal is properly fitted
            this.connect();
        }, fitDelay);

        // Handle terminal input
        this.term.onData((data) => {
            this.handleTerminalInput(data);
        });

        // Handle window resize with debouncing
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.fitAddon.fit();
                this.sendTerminalSize();
            }, 150);
        });

        // Handle orientation change on mobile
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.fitAddon.fit();
                this.sendTerminalSize();
            }, 200);
        });

        // Handle iOS keyboard show/hide using visualViewport
        if (window.visualViewport) {
            let keyboardVisible = false;

            window.visualViewport.addEventListener('resize', () => {
                // Detect keyboard state
                const viewportHeight = window.visualViewport.height;
                const windowHeight = window.innerHeight;
                const newKeyboardVisible = viewportHeight < windowHeight * 0.75;

                if (newKeyboardVisible !== keyboardVisible) {
                    keyboardVisible = newKeyboardVisible;

                    // Resize terminal when keyboard state changes
                    setTimeout(() => {
                        this.fitAddon.fit();
                        this.sendTerminalSize();

                        // Scroll to cursor when keyboard appears
                        if (keyboardVisible) {
                            this.scrollToCursor();
                        }
                    }, 100);
                }
            });
        }

        // Mobile-specific: enhance touch scrolling
        if (isMobile) {
            const viewport = container.querySelector('.xterm-viewport');
            if (viewport) {
                // Prevent scroll interference
                viewport.addEventListener('touchstart', (e) => {
                    // Allow native scroll to work
                    e.stopPropagation();
                }, { passive: true });

                viewport.addEventListener('touchmove', (e) => {
                    e.stopPropagation();
                }, { passive: true });
            }
        }

        // NOTE: Connect is now called after initial fit (see setTimeout above)
    }

    loadSessionFromStorage() {
        try {
            const stored = localStorage.getItem('claude_session_id');
            if (stored) {
                this.sessionId = stored;
                console.log(`[SESSION] Loaded session ID from storage: ${this.sessionId}`);
            }
        } catch (e) {
            console.warn('[SESSION] localStorage not available:', e);
        }
    }

    saveSessionToStorage(sessionId) {
        try {
            localStorage.setItem('claude_session_id', sessionId);
            console.log(`[SESSION] Saved session ID to storage: ${sessionId}`);
        } catch (e) {
            console.warn('[SESSION] Failed to save session ID:', e);
        }
    }

    clearSessionFromStorage() {
        try {
            localStorage.removeItem('claude_session_id');
            console.log('[SESSION] Cleared session ID from storage');
        } catch (e) {
            console.warn('[SESSION] Failed to clear session ID:', e);
        }
    }

    connect() {
        if (this.ws) {
            this.ws.close();
        }

        this.updateStatus('Connecting...', 'connecting');

        try {
            // Build WebSocket URL with session ID if available
            let wsUrl = this.wsUrl;
            if (this.sessionId) {
                wsUrl += `?session_id=${this.sessionId}`;
                console.log(`[WS] Connecting with session ID: ${this.sessionId}`);
            }

            this.ws = new WebSocket(wsUrl);
            this.ws.binaryType = 'arraybuffer';

            this.ws.onopen = () => this.onOpen();
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onclose = (event) => this.onClose(event);

        } catch (error) {
            console.error('[WS] Connection error:', error);
            this.scheduleReconnect();
        }
    }

    onOpen() {
        console.log('[WS] Connected');
        this.connected = true;
        this.currentReconnectDelay = this.reconnectBaseDelay;
        this.updateStatus('Connected', 'connected');

        // Send initial terminal dimensions after a brief delay
        // to ensure terminal has fully rendered
        setTimeout(() => {
            this.sendTerminalSize();
        }, 100);

        // Start heartbeat
        this.startHeartbeat();

        // Flush input queue
        this.flushInputQueue();
    }

    onMessage(event) {
        try {
            // Decode binary frame to JSON
            let message;
            if (event.data instanceof ArrayBuffer) {
                const text = new TextDecoder().decode(event.data);
                message = JSON.parse(text);
            } else {
                message = JSON.parse(event.data);
            }

            const msgType = message.type;

            // DEBUG: Log all messages
            console.log(`[WS MSG] Type: ${msgType}, Length: ${message.text?.length || 0}`);

            if (msgType === 'session') {
                // Handle session ID assignment/reconnection
                const sessionId = message.session_id;
                const reconnected = message.reconnected || false;
                const ageSeconds = message.age_seconds || 0;

                console.log(`[SESSION] Received session ID: ${sessionId}, reconnected: ${reconnected}`);

                // Store session ID
                this.sessionId = sessionId;
                this.saveSessionToStorage(sessionId);

                // Show reconnection notification if applicable
                if (reconnected) {
                    this.showReconnectNotification(ageSeconds);
                }

            } else if (msgType === 'output') {
                // DEBUG: Log output details
                console.log(`[WS OUTPUT] Writing ${message.text.length} chars:`, message.text.substring(0, 50));

                const isReplay = message.is_replay || false;

                if (isReplay) {
                    // Clear terminal before replaying history
                    console.log('[WS OUTPUT] Replaying session history...');
                    this.term.clear();
                    this.term.write(message.text);
                    this.showReplayComplete();
                } else {
                    // Live output
                    this.term.write(message.text);
                }

            } else if (msgType === 'theme') {
                console.log('[WS THEME] Applying theme');
                // Apply theme from server
                this.applyTheme(message);

            } else if (msgType === 'ping') {
                console.log('[WS PING] Responding with pong');
                // Respond to heartbeat ping
                this.sendMessage({ type: 'pong' });

            } else {
                console.log('[WS] Unknown message type:', msgType);
            }

        } catch (error) {
            console.error('[WS] Message parse error:', error);
        }
    }

    onError(error) {
        console.error('[WS] Error:', error);
        this.updateStatus('Error', 'error');
    }

    onClose(event) {
        console.log('[WS] Disconnected:', event.code, event.reason);
        this.connected = false;
        this.updateStatus('Disconnected', 'disconnected');

        // Stop heartbeat
        this.stopHeartbeat();

        // Schedule reconnect
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        // Calculate delay with jitter
        const jitter = 1 + (Math.random() * 2 - 1) * this.reconnectJitter;
        const delay = Math.min(
            this.currentReconnectDelay * jitter,
            this.reconnectMaxDelay
        );

        console.log(`[WS] Reconnecting in ${Math.round(delay)}ms...`);
        this.updateStatus(`Reconnecting in ${Math.round(delay / 1000)}s...`, 'reconnecting');

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);

        // Increase delay for next attempt (exponential backoff)
        this.currentReconnectDelay = Math.min(
            this.currentReconnectDelay * this.reconnectDecay,
            this.reconnectMaxDelay
        );
    }

    startHeartbeat() {
        this.stopHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            if (this.connected) {
                // Server sends ping, we just need to respond with pong
                // No action needed here, handled in onMessage
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    handleTerminalInput(data) {
        if (this.connected) {
            this.sendMessage({
                type: 'input',
                text: data
            });
        } else {
            // Queue input during disconnect
            if (this.inputQueue.length < this.maxQueueSize) {
                this.inputQueue.push(data);
            }
        }
    }

    flushInputQueue() {
        while (this.inputQueue.length > 0) {
            const data = this.inputQueue.shift();
            this.sendMessage({
                type: 'input',
                text: data
            });
        }
    }

    sendMessage(message) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('[WS] Cannot send, not connected');
            return;
        }

        try {
            // Encode as binary frame for efficiency
            const json = JSON.stringify(message);
            const encoded = new TextEncoder().encode(json);
            this.ws.send(encoded);
        } catch (error) {
            console.error('[WS] Send error:', error);
        }
    }

    sendTerminalSize() {
        if (!this.term || !this.connected) {
            return;
        }

        const rows = this.term.rows;
        const cols = this.term.cols;

        console.log(`[RESIZE] Sending terminal size: ${rows}x${cols}`);

        this.sendMessage({
            type: 'resize',
            rows: rows,
            cols: cols
        });
    }

    applyTheme(themeConfig) {
        console.log('[THEME] Applying theme:', themeConfig);
        this.themeConfig = themeConfig;

        // Update terminal theme
        if (themeConfig.colors) {
            this.term.options.theme = themeConfig.colors;
        }

        // Update font (with fallback)
        if (themeConfig.font) {
            // Use monospace fallback for better mobile rendering
            this.term.options.fontFamily = `"${themeConfig.font}", Menlo, Monaco, "Courier New", monospace`;
        }

        // Update font size (scale down on mobile if too large)
        if (themeConfig.fontSize) {
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            const maxMobileFontSize = 14; // Much smaller to prevent wrapping

            let fontSize = themeConfig.fontSize;
            if (isMobile && fontSize > maxMobileFontSize) {
                fontSize = maxMobileFontSize;
                console.log(`[THEME] Scaled down font size from ${themeConfig.fontSize} to ${fontSize} for mobile`);
            }

            this.term.options.fontSize = fontSize;
        }

        // Force a complete re-render and re-fit
        setTimeout(() => {
            this.term.refresh(0, this.term.rows - 1);
            this.fitAddon.fit();

            // Double-check fit after a moment and send new size
            setTimeout(() => {
                this.fitAddon.fit();
                // CRITICAL: Send new terminal size after theme changes font
                this.sendTerminalSize();
            }, 100);
        }, 50);
    }

    updateStatus(text, statusClass) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = text;
            statusEl.className = statusClass;
        }
    }

    showReconnectNotification(ageSeconds) {
        const minutes = Math.floor(ageSeconds / 60);
        const seconds = Math.floor(ageSeconds % 60);

        let timeStr;
        if (minutes > 0) {
            timeStr = `${minutes}m ${seconds}s`;
        } else {
            timeStr = `${seconds}s`;
        }

        const message = `Reconnected to session (${timeStr} old)`;
        this.showToast(message, 3000);
    }

    showReplayComplete() {
        this.showToast('History restored', 2000);
    }

    showToast(message, duration = 3000) {
        const toast = document.getElementById('reconnect-toast');
        const messageEl = document.getElementById('reconnect-message');

        if (!toast || !messageEl) {
            console.warn('[TOAST] Toast elements not found in DOM');
            return;
        }

        messageEl.textContent = message;
        toast.classList.remove('hidden');

        // Auto-hide after duration
        setTimeout(() => {
            toast.classList.add('hidden');
        }, duration);
    }

    showLoadingOverlay(message = 'Restoring session...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');

        if (overlay) {
            if (messageEl) {
                messageEl.textContent = message;
            }
            overlay.classList.remove('hidden');
        }
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    clearSession() {
        console.log('[SESSION] Clearing session and starting fresh...');

        // Clear session ID from storage
        this.clearSessionFromStorage();
        this.sessionId = null;

        // Close current connection
        if (this.ws) {
            this.ws.close();
        }

        // Clear terminal
        if (this.term) {
            this.term.clear();
        }

        // Reconnect with new session
        this.connect();

        this.showToast('Started new session', 2000);
    }

    scrollToCursor() {
        // Scroll terminal to show cursor position
        if (this.term && this.term.buffer) {
            const cursorY = this.term.buffer.active.cursorY;
            const viewport = document.querySelector('.xterm-viewport');

            if (viewport) {
                // Scroll to show cursor with some padding
                const lineHeight = this.term._core._renderService.dimensions.actualCellHeight;
                const scrollTop = (cursorY - 5) * lineHeight; // 5 lines of padding
                viewport.scrollTop = Math.max(0, scrollTop);
            }
        }
    }

    destroy() {
        this.stopHeartbeat();

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        if (this.ws) {
            this.ws.close();
        }

        if (this.term) {
            this.term.dispose();
        }
    }
}

// Initialize terminal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[APP] Initializing Claude terminal...');
    window.claudeTerminal = new ClaudeTerminal();
});
