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
        this.connecting = false;  // Guard against duplicate connection attempts

        // Reconnection config
        this.reconnectBaseDelay = 1000;      // 1s base
        this.reconnectMaxDelay = 30000;       // 30s max
        this.reconnectDecay = 1.5;            // 1.5x multiplier
        this.reconnectJitter = 0.3;           // ±30% jitter
        this.currentReconnectDelay = this.reconnectBaseDelay;
        this.reconnectTimer = null;
        this.reconnectAttempts = 0;           // Track failed attempts
        this.maxReconnectBeforeReset = 3;     // Clear session after 3 failed attempts

        // Circuit breaker to prevent infinite reconnection loop
        this.maxConsecutiveFailures = 5;     // Stop after 5 consecutive failures
        this.consecutiveFailures = 0;         // Counter for consecutive failures
        this.circuitBreakerTripped = false;   // Circuit breaker state

        // Error diagnostics tracking
        this.errorHistory = [];               // Last 10 errors with full context
        this.maxErrorHistory = 10;            // Keep last 10 errors
        this.lastErrorDetails = null;         // Most recent error for UI display

        // Heartbeat config
        this.heartbeatInterval = 30000;       // 30s
        this.heartbeatTimer = null;

        // Launch screen timer
        this.launchTimer = null;

        // Connection timeout (prevent indefinite hanging)
        this.connectionTimeout = null;
        this.connectionTimeoutDuration = 30000; // 30 seconds

        // Stuck connection timeout (detect when connected but no output)
        this.stuckConnectionTimer = null;
        this.stuckConnectionTimeout = 15000; // 15 seconds after connection

        // Terminal
        this.term = null;
        this.fitAddon = null;

        // Theme config (will be sent by server)
        this.themeConfig = null;

        // Input queue (for buffering during disconnect)
        this.inputQueue = [];
        this.maxQueueSize = 100;

        // Smart scroll debouncing
        this.scrollDebounceTimer = null;
        this.scrollDebounceDelay = 100; // 100ms debounce for smooth streaming

        // Initial load tracking (for scroll behavior)
        this.isInitialLoad = true; // Force scroll to bottom on first load
        this.hasReceivedFirstOutput = false; // Track first output for launching screen

        // Connection timing diagnostics
        this.connectionStartTime = null;
        this.timingMarkers = {}; // Store timing for each stage

        this.init();
    }

    init() {
        // Start timing diagnostics
        this.connectionStartTime = Date.now();
        this.logTiming('init_start', 'Initializing terminal');

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
            this.logTiming('terminal_fit', 'Terminal fit complete');
            console.log('[INIT] Initial terminal fit...');
            this.fitAddon.fit();
            console.log(`[INIT] Terminal sized to ${this.term.rows}x${this.term.cols}`);

            // iOS Safari WebSocket restriction workaround
            // Smart auto-connect: prioritize session persistence over first-time tap
            // NOTE: Overlay is already visible by default (progressive enhancement)
            // We just need to update text and behavior appropriately
            if (isMobile) {
                const hasSession = this.sessionId !== null;
                const hasConnectedBefore = this.getConnectionPermission();

                if (hasSession) {
                    // Has active session - show launching screen with auto-connect
                    console.log('[INIT] Found existing session - updating overlay for reconnection');
                    this.showLaunchingScreen(true);
                } else if (hasConnectedBefore) {
                    // User has connected before but no active session - show launching screen
                    console.log('[INIT] Returning mobile user - updating overlay for reconnection');
                    this.showLaunchingScreen(true);
                } else {
                    // True first-time visitor - overlay is already showing "Loading...", update to tap mode
                    console.log('[INIT] First mobile visit - updating overlay for tap-to-connect');
                    this.showTapToConnect();
                }
            } else {
                // Desktop - hide overlay immediately and auto-connect
                console.log('[INIT] Desktop detected - hiding overlay and connecting');
                const overlay = document.getElementById('tap-to-connect');
                if (overlay) {
                    overlay.classList.add('hidden');
                }
                this.connect();
            }
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

        // Phase 2: Page Visibility API for session resurrection
        // Automatically reconnect when user returns to the app
        this.setupVisibilityHandler();

        // Mobile keyboard toolbar setup
        if (isMobile) {
            this.setupKeyboardToolbar();
        }
    }

    setupVisibilityHandler() {
        // Phase 2 & 3: Handle app switching and backgrounding with iOS-specific events

        // Track background state
        let wasConnectedBeforeBackground = false;

        // Standard visibility change (works on all platforms)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // App went to background
                console.log('[VISIBILITY] App backgrounded - pausing heartbeat');
                wasConnectedBeforeBackground = this.connected;
                // Don't close connection immediately - give user time to return
                this.stopHeartbeat();
            } else {
                // App returned to foreground
                console.log('[VISIBILITY] App foregrounded - checking connection');

                if (!this.connected && this.sessionId) {
                    // Connection lost while backgrounded - show launching screen
                    console.log('[VISIBILITY] Reconnecting after app switch');
                    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                    if (isMobile) {
                        this.showLaunchingScreen(true);
                    } else {
                        this.connect();
                    }
                } else if (this.connected) {
                    // Still connected - restart heartbeat
                    console.log('[VISIBILITY] Connection maintained - resuming heartbeat');
                    this.startHeartbeat();
                } else if (!this.sessionId) {
                    // No session at all - this is expected for first-time users
                    console.log('[VISIBILITY] No session to reconnect');
                }
            }
        });

        // Phase 3: iOS-specific events for better background detection
        // pageshow/pagehide are more reliable on iOS Safari
        window.addEventListener('pagehide', () => {
            console.log('[PAGEHIDE] iOS page suspended');
            wasConnectedBeforeBackground = this.connected;
            this.stopHeartbeat();
        });

        window.addEventListener('pageshow', (event) => {
            console.log('[PAGESHOW] iOS page resumed', { persisted: event.persisted });

            if (event.persisted) {
                // Page was restored from bfcache (back/forward cache)
                // This happens when using iOS multitasking or switching tabs
                console.log('[PAGESHOW] Restored from bfcache - checking connection');

                if (!this.connected && this.sessionId) {
                    console.log('[PAGESHOW] Reconnecting after bfcache restore');
                    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                    if (isMobile) {
                        this.showLaunchingScreen(true);
                    } else {
                        this.connect();
                    }
                } else if (this.connected) {
                    this.startHeartbeat();
                }
            }
        });

        // Phase 3: Handle focus/blur for additional resilience
        window.addEventListener('focus', () => {
            console.log('[FOCUS] Window gained focus');
            if (!this.connected && this.sessionId) {
                console.log('[FOCUS] Reconnecting on window focus');
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                if (isMobile) {
                    this.showLaunchingScreen(true);
                } else {
                    this.connect();
                }
            }
        });

        window.addEventListener('blur', () => {
            console.log('[BLUR] Window lost focus');
            // Don't do anything drastic - just log
        });

        console.log('[VISIBILITY] Complete visibility/background management initialized');
    }

    setupKeyboardToolbar() {
        const toolbar = document.getElementById('keyboard-toolbar');
        if (!toolbar) {
            console.warn('[TOOLBAR] Keyboard toolbar element not found');
            return;
        }

        // DON'T show toolbar yet - wait until connection succeeds
        // This prevents toolbar from showing during connection/error states
        console.log('[TOOLBAR] Toolbar initialized (hidden until connected)');

        // Special key sequences
        const keySequences = {
            'tab': '\t',                // Tab key
            'shift-tab': '\x1b[Z',      // Shift+Tab (backtab) for cycling backwards
            'ctrl-c': '\x03',           // Ctrl+C (SIGINT)
            'esc': '\x1b',              // Escape key
        };

        // Handle button clicks
        toolbar.querySelectorAll('.key-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const key = button.getAttribute('data-key');
                const sequence = keySequences[key];

                if (sequence) {
                    console.log(`[TOOLBAR] Sending key: ${key}`);
                    this.handleTerminalInput(sequence);

                    // Visual feedback
                    button.style.background = 'rgba(183, 168, 255, 0.5)';
                    setTimeout(() => {
                        button.style.background = '';
                    }, 150);
                } else {
                    console.warn(`[TOOLBAR] Unknown key: ${key}`);
                }
            });
        });

        console.log('[TOOLBAR] Mobile keyboard toolbar initialized');
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

    // Storage helpers with sessionStorage fallback for private mode
    getConnectionPermission() {
        // Try localStorage first, fallback to sessionStorage if it fails (private mode)
        try {
            const value = localStorage.getItem('claude_has_connected');
            if (value) {
                console.log('[STORAGE] Connection permission retrieved from localStorage');
                return value;
            }
        } catch (e) {
            console.warn('[STORAGE] localStorage unavailable, trying sessionStorage:', e);
        }

        // Fallback to sessionStorage
        try {
            const value = sessionStorage.getItem('claude_has_connected');
            if (value) {
                console.log('[STORAGE] Connection permission retrieved from sessionStorage (private mode)');
                return value;
            }
        } catch (e) {
            console.warn('[STORAGE] sessionStorage also unavailable:', e);
        }

        return null;
    }

    setConnectionPermission(value) {
        // Try localStorage first, fallback to sessionStorage if it fails (private mode)
        try {
            localStorage.setItem('claude_has_connected', value);
            console.log('[STORAGE] Connection permission saved to localStorage');
            return true;
        } catch (e) {
            console.warn('[STORAGE] localStorage unavailable, trying sessionStorage:', e);
        }

        // Fallback to sessionStorage
        try {
            sessionStorage.setItem('claude_has_connected', value);
            console.log('[STORAGE] Connection permission saved to sessionStorage (private mode)');
            return true;
        } catch (e) {
            console.error('[STORAGE] Both localStorage and sessionStorage unavailable:', e);
            return false;
        }
    }

    getCloseCodeDescription(code) {
        // Map WebSocket close codes to human-readable descriptions
        const codes = {
            1000: 'Normal Closure',
            1001: 'Going Away',
            1002: 'Protocol Error',
            1003: 'Unsupported Data',
            1004: 'Reserved',
            1005: 'No Status Received',
            1006: 'Abnormal Closure',
            1007: 'Invalid Frame Payload Data',
            1008: 'Policy Violation',
            1009: 'Message Too Big',
            1010: 'Mandatory Extension',
            1011: 'Internal Server Error',
            1012: 'Service Restart',
            1013: 'Try Again Later',
            1014: 'Bad Gateway',
            1015: 'TLS Handshake Failure'
        };

        const description = codes[code] || `Unknown Code (${code})`;

        // Add helpful context for common issues
        if (code === 1006) {
            return `${description} - Connection never established or lost unexpectedly`;
        } else if (code === 1001) {
            return `${description} - Server is shutting down or client navigated away`;
        } else if (code === 1011) {
            return `${description} - Server encountered an error`;
        }

        return description;
    }

    getDiagnostics() {
        // Gather comprehensive diagnostic information
        const diagnostics = {
            timestamp: new Date().toISOString(),
            url: this.wsUrl + (this.sessionId ? `?session_id=${this.sessionId}` : ''),
            online: navigator.onLine,
            readyState: this.ws ? this.ws.readyState : null,
            readyStateText: this.ws ? ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][this.ws.readyState] : 'NOT_CREATED',
            connectionStatus: {
                connected: this.connected,
                reconnectAttempts: this.reconnectAttempts,
                consecutiveFailures: this.consecutiveFailures,
                circuitBreakerTripped: this.circuitBreakerTripped
            },
            lastError: this.lastErrorDetails,
            recentErrors: this.errorHistory.slice(-5),
            browser: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language
            },
            session: {
                hasSession: !!this.sessionId,
                sessionId: this.sessionId ? this.sessionId.substring(0, 8) + '...' : null
            }
        };

        return diagnostics;
    }

    logDiagnostics() {
        const diag = this.getDiagnostics();
        console.group('%c[DIAGNOSTICS] Connection Status', 'color: #f59e0b; font-weight: bold');
        console.log('URL:', diag.url);
        console.log('WebSocket State:', diag.readyStateText);
        console.log('Online:', diag.online);
        console.log('Connection:', diag.connectionStatus);
        if (diag.lastError) {
            console.log('Last Error:', diag.lastError);
        }
        if (diag.recentErrors.length > 0) {
            console.log('Recent Errors:', diag.recentErrors);
        }
        console.groupEnd();
    }

    connect() {
        // Guard: Prevent duplicate connection attempts
        if (this.connecting) {
            console.log('[WS] Connection already in progress - skipping duplicate attempt');
            return;
        }

        if (this.connected) {
            console.log('[WS] Already connected - skipping duplicate attempt');
            return;
        }

        this.logTiming('connect_start', 'Initiating WebSocket connection');
        console.log('[WS] Initiating connection attempt');
        this.connecting = true;

        // Close existing WebSocket if any
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

            // Set connection timeout to prevent indefinite hanging
            this.connectionTimeout = setTimeout(() => {
                if (this.connecting && !this.connected) {
                    console.error(`[WS] Connection timeout after ${this.connectionTimeoutDuration / 1000}s`);
                    console.error('[WS] Network may be slow or server unreachable');

                    // Close the WebSocket if still trying
                    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
                        this.ws.close();
                    }

                    this.connecting = false;
                    this.consecutiveFailures++;

                    // Show error if circuit breaker triggers
                    if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
                        this.circuitBreakerTripped = true;
                        this.showConnectionFailed();
                    } else {
                        // Otherwise schedule reconnect
                        this.scheduleReconnect();
                    }
                }
            }, this.connectionTimeoutDuration);

            console.log(`[WS] Connection timeout set: ${this.connectionTimeoutDuration / 1000}s`);

        } catch (error) {
            console.error('[WS] Connection error:', error);
            this.connecting = false;

            // Clear timeout on error
            if (this.connectionTimeout) {
                clearTimeout(this.connectionTimeout);
                this.connectionTimeout = null;
            }

            this.scheduleReconnect();
        }
    }

    onOpen() {
        this.logTiming('websocket_open', 'WebSocket connected');
        console.log('[WS] Connected');
        this.connected = true;
        this.connecting = false;  // Connection successful, clear guard
        this.currentReconnectDelay = this.reconnectBaseDelay;
        this.reconnectAttempts = 0;  // Reset failed attempts on successful connection
        this.consecutiveFailures = 0;  // Reset circuit breaker counter
        this.circuitBreakerTripped = false;  // Reset circuit breaker state

        // Clear connection timeout (connection succeeded)
        if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
            console.log('[WS] Cleared connection timeout (connected successfully)');
        }

        // Mark that user has connected (for future auto-connect on mobile)
        // This ensures reconnections don't require tap, even if session expires
        this.setConnectionPermission('true');
        console.log('[WS] Stored connection permission for future auto-connect');

        // Clear launch timer if it exists (connection succeeded before timer fired)
        if (this.launchTimer) {
            console.log('[WS] Clearing launch timer (connection succeeded)');
            clearTimeout(this.launchTimer);
            this.launchTimer = null;
        }

        // DON'T hide launch overlay yet - wait for first output from Claude
        // This prevents black screen during Claude startup (can take 5-15 seconds)
        console.log('[WS] Connection established - waiting for first output...');

        // Start timeout to update launching message if Claude is slow to start
        this.claudeStartupTimer = setTimeout(() => {
            const overlay = document.getElementById('tap-to-connect');
            const messageEl = document.getElementById('tap-message');
            if (overlay && !overlay.classList.contains('hidden') && messageEl) {
                messageEl.textContent = 'Starting Claude... (this may take a moment)';
                console.log('[WS] Claude startup taking longer than expected - updated message');
            }
        }, 3000); // 3 second timeout

        // Start stuck connection timeout (15s)
        // If we don't receive ANY output after 15s, something is wrong
        this.stuckConnectionTimer = setTimeout(() => {
            // Only show error if we still haven't received first output
            if (!this.hasReceivedFirstOutput) {
                console.error('[WS] Stuck connection detected - no output after 15s');
                const overlay = document.getElementById('tap-to-connect');
                const messageEl = document.getElementById('tap-message');
                if (overlay && !overlay.classList.contains('hidden') && messageEl) {
                    messageEl.textContent = 'Connection seems stuck. Check that Claude Code is running on your Mac.';
                    messageEl.style.color = '#ef4444'; // Red color for error
                    console.log('[WS] Updated overlay with stuck connection error');
                }
            }
        }, this.stuckConnectionTimeout);

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

        // Focus terminal once connection is established
        // This makes terminal immediately interactive without requiring tap
        try {
            this.term.focus();
            console.log('[TERM] Auto-focused terminal on connection');
        } catch (e) {
            console.warn('[TERM] Failed to focus terminal:', e);
        }

        // Show keyboard toolbar now that connection is established
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (isMobile) {
            const toolbar = document.getElementById('keyboard-toolbar');
            if (toolbar) {
                toolbar.classList.remove('hidden');
                console.log('[TOOLBAR] Showing toolbar (connection established)');
            }
        }
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

                // Reconnection notification removed per user feedback
                // User doesn't want the "Reconnected Xs old" toast bubble
                if (reconnected) {
                    console.log(`[SESSION] Reconnected to session (${ageSeconds}s old) - notification suppressed`);
                    // this.showReconnectNotification(ageSeconds); // REMOVED
                }

            } else if (msgType === 'output') {
                // DEBUG: Log output details with diagnostics
                if (message.text === null || message.text === undefined) {
                    console.warn('[WS OUTPUT] Received output message with missing text field:', JSON.stringify(message));
                }
                const preview = (message.text || '').substring(0, 50);
                console.log(`[WS OUTPUT] Writing ${(message.text || '').length} chars:`, preview || '(empty)');

                const isReplay = message.is_replay || false;

                // Hide launching screen on FIRST output (prevents black screen during Claude startup)
                if (!this.hasReceivedFirstOutput) {
                    this.hasReceivedFirstOutput = true;
                    this.logTiming('first_output', 'First output received from Claude');

                    // Clear Claude startup timer
                    if (this.claudeStartupTimer) {
                        clearTimeout(this.claudeStartupTimer);
                        this.claudeStartupTimer = null;
                    }

                    // Clear stuck connection timer (got output, connection is working)
                    if (this.stuckConnectionTimer) {
                        clearTimeout(this.stuckConnectionTimer);
                        this.stuckConnectionTimer = null;
                        console.log('[WS] Cleared stuck connection timer (first output received)');
                    }

                    // Hide launch overlay now that we have content
                    const overlay = document.getElementById('tap-to-connect');
                    if (overlay && !overlay.classList.contains('hidden')) {
                        console.log('[WS] Hiding launch overlay (first output received)');
                        overlay.classList.add('hidden');
                    }
                }

                if (isReplay) {
                    // Replay session history (don't clear terminal - just append)
                    console.log('[WS OUTPUT] Replaying session history...');
                    // Don't clear! Just append the buffered output
                    this.term.write(message.text);
                    this.showReplayComplete();
                    // Scroll to show restored history - wait for DOM paint with requestAnimationFrame
                    requestAnimationFrame(() => {
                        setTimeout(() => this.scrollToFollow(), 50);
                    });
                } else {
                    // Live output - write first, THEN schedule scroll
                    this.term.write(message.text);

                    // On first output (initial banner load), force immediate scroll after DOM paint
                    // This prevents blank cursor screen on fresh load
                    if (this.isInitialLoad) {
                        requestAnimationFrame(() => {
                            setTimeout(() => this.scrollToFollow(), 50);
                        });
                    } else {
                        // Normal operation: use debounced scroll for smooth streaming
                        this.scheduleSmoothScroll();
                    }
                }

            } else if (msgType === 'theme') {
                console.log('[WS THEME] Applying theme');
                // Apply theme from server
                this.applyTheme(message);

            } else if (msgType === 'ping') {
                console.log('[WS PING] Responding with pong');
                // Respond to heartbeat ping
                this.sendMessage({ type: 'pong' });

            } else if (msgType === 'pong') {
                // Silently accept pong messages from server
                // (We send pong in response to ping, but shouldn't normally receive pong)
                // This prevents "Unknown message type" errors in console

            } else if (msgType === 'error') {
                const errorMsg = message.text || message.message || '(no error message)';
                console.error('[WS ERROR]', errorMsg);
                // Log full message structure for debugging if no text/message
                if (!message.text && !message.message) {
                    console.error('[WS ERROR] Missing error message. Full message:', JSON.stringify(message));
                }
                this.term.write(`\r\n\x1b[31mError: ${errorMsg}\x1b[0m\r\n`);

            } else {
                console.log('[WS] Unknown message type:', msgType, 'Full message:', JSON.stringify(message));
            }

        } catch (error) {
            console.error('[WS] Message parse error:', error);
            console.error('[WS] Raw event data:', event.data);
        }
    }

    onError(error) {
        // Clear connection timeout (error occurred)
        if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
            console.log('[WS] Cleared connection timeout (error occurred)');
        }

        // Clear stuck connection timer (error occurred before output)
        if (this.stuckConnectionTimer) {
            clearTimeout(this.stuckConnectionTimer);
            this.stuckConnectionTimer = null;
            console.log('[WS] Cleared stuck connection timer (error occurred)');
        }

        // Capture comprehensive error diagnostics
        const errorDetails = {
            timestamp: new Date().toISOString(),
            type: 'error',
            url: this.wsUrl + (this.sessionId ? `?session_id=${this.sessionId}` : ''),
            readyState: this.ws ? this.ws.readyState : null,
            readyStateText: this.ws ? ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][this.ws.readyState] : 'NOT_CREATED',
            online: navigator.onLine,
            attempt: this.reconnectAttempts + 1,
            consecutiveFailures: this.consecutiveFailures + 1,
            error: {
                // WebSocket errors are minimal in browsers for security
                type: error.type,
                isTrusted: error.isTrusted,
                message: 'WebSocket error (details unavailable in browser)'
            }
        };

        // Store in error history
        this.errorHistory.push(errorDetails);
        if (this.errorHistory.length > this.maxErrorHistory) {
            this.errorHistory.shift(); // Remove oldest
        }

        this.lastErrorDetails = errorDetails;

        // Enhanced console logging with grouped output
        console.group('%c[WS ERROR] Connection Attempt Failed', 'color: #ef4444; font-weight: bold');
        console.log('Timestamp:', errorDetails.timestamp);
        console.log('URL:', errorDetails.url);
        console.log('WebSocket State:', `${errorDetails.readyStateText} (${errorDetails.readyState})`);
        console.log('Network Online:', errorDetails.online);
        console.log('Attempt:', errorDetails.attempt);
        console.log('Consecutive Failures:', errorDetails.consecutiveFailures + '/' + this.maxConsecutiveFailures);
        console.log('Error Event:', error);

        // Provide troubleshooting hints
        if (!errorDetails.online) {
            console.warn('💡 Device appears offline - check network connection');
        } else if (errorDetails.readyState === 0) {
            console.warn('💡 Connection never established - server may be unreachable or refusing connections');
        }

        console.groupEnd();

        this.updateStatus('Error', 'error');
    }

    onClose(event) {
        // Clear connection timeout (connection closed)
        if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
            console.log('[WS] Cleared connection timeout (connection closed)');
        }

        // Clear stuck connection timer (connection closed before output)
        if (this.stuckConnectionTimer) {
            clearTimeout(this.stuckConnectionTimer);
            this.stuckConnectionTimer = null;
            console.log('[WS] Cleared stuck connection timer (connection closed)');
        }

        // Capture comprehensive close event diagnostics
        const closeDetails = {
            timestamp: new Date().toISOString(),
            type: 'close',
            url: this.wsUrl + (this.sessionId ? `?session_id=${this.sessionId}` : ''),
            code: event.code,
            codeDescription: this.getCloseCodeDescription(event.code),
            reason: event.reason || '(no reason provided)',
            wasClean: event.wasClean,
            online: navigator.onLine,
            attempt: this.reconnectAttempts + 1,
            consecutiveFailures: this.consecutiveFailures + 1
        };

        // Store in error history
        this.errorHistory.push(closeDetails);
        if (this.errorHistory.length > this.maxErrorHistory) {
            this.errorHistory.shift(); // Remove oldest
        }

        this.lastErrorDetails = closeDetails;

        // Enhanced console logging with grouped output
        console.group('%c[WS CLOSE] Connection Closed', 'color: #f59e0b; font-weight: bold');
        console.log('Timestamp:', closeDetails.timestamp);
        console.log('Close Code:', `${event.code} - ${closeDetails.codeDescription}`);
        console.log('Reason:', closeDetails.reason);
        console.log('Clean Closure:', closeDetails.wasClean);
        console.log('Network Online:', closeDetails.online);
        console.log('Attempt:', closeDetails.attempt);
        console.log('Consecutive Failures:', closeDetails.consecutiveFailures + '/' + this.maxConsecutiveFailures);

        // Provide troubleshooting hints based on close code
        if (event.code === 1006) {
            console.warn('💡 Abnormal closure - connection never established or lost unexpectedly');
            console.warn('   Common causes:');
            console.warn('   • Server not running or unreachable');
            console.warn('   • Firewall blocking port 8000');
            console.warn('   • Network connectivity issues');
            console.warn('   • DNS resolution failed for hostname');
        } else if (event.code === 1011) {
            console.warn('💡 Server error - check backend logs for details');
        } else if (!closeDetails.online) {
            console.warn('💡 Device appears offline - check network connection');
        }

        console.groupEnd();

        this.connected = false;
        this.connecting = false;  // Clear guard on disconnect
        this.updateStatus('Disconnected', 'disconnected');

        // Clear launch timer before scheduling reconnect to prevent conflicts
        if (this.launchTimer) {
            console.log('[WS] Clearing launch timer (connection closed)');
            clearTimeout(this.launchTimer);
            this.launchTimer = null;
        }

        // Stop heartbeat
        this.stopHeartbeat();

        // Schedule reconnect
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        // Clear any existing timers to prevent conflicts
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        // Clear launch timer if it exists (take control of reconnection)
        if (this.launchTimer) {
            console.log('[RECONNECT] Clearing launch timer (taking over reconnection)');
            clearTimeout(this.launchTimer);
            this.launchTimer = null;
        }

        // Don't schedule reconnect if already connecting
        if (this.connecting) {
            console.log('[RECONNECT] Connection already in progress - skipping schedule');
            return;
        }

        // Increment failed attempts counters
        this.reconnectAttempts++;
        this.consecutiveFailures++;

        // Circuit breaker: Stop after too many consecutive failures
        if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
            console.error(`[CIRCUIT BREAKER] Tripped after ${this.consecutiveFailures} consecutive failures`);
            this.circuitBreakerTripped = true;
            this.showConnectionFailed();
            return; // Stop reconnection loop
        }

        // AUTOMATIC SESSION RESET: After multiple failures, clear stale session and try fresh
        if (this.reconnectAttempts >= this.maxReconnectBeforeReset && this.sessionId) {
            console.warn(`[WS] ${this.reconnectAttempts} failed reconnection attempts - clearing stale session`);
            this.clearSessionFromStorage();
            this.sessionId = null;
            this.showToast('Retrying with fresh session...', 3000);
        }

        // Calculate delay with jitter
        const jitter = 1 + (Math.random() * 2 - 1) * this.reconnectJitter;
        const delay = Math.min(
            this.currentReconnectDelay * jitter,
            this.reconnectMaxDelay
        );

        console.log(`[WS] Reconnecting in ${Math.round(delay)}ms... (attempt ${this.reconnectAttempts}, failures: ${this.consecutiveFailures}/${this.maxConsecutiveFailures})`);
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

    showReconnectingToast() {
        // Show brief "Reconnecting..." toast instead of full-screen overlay
        this.showToast('Reconnecting to session...', 2000);
    }

    showLaunchingScreen(isReconnect = false) {
        // Guard: Don't show if already connected or connecting
        if (this.connected) {
            console.log('[LAUNCH] Already connected - skipping launch screen');
            return;
        }

        if (this.connecting) {
            console.log('[LAUNCH] Connection in progress - skipping launch screen');
            return;
        }

        const overlay = document.getElementById('tap-to-connect');
        const titleEl = document.getElementById('tap-title');
        const messageEl = document.getElementById('tap-message');
        const hintEl = document.getElementById('tap-hint');

        if (!overlay) {
            console.warn('[LAUNCH] Tap overlay element not found');
            // Fallback to auto-connect if overlay missing
            this.connect();
            return;
        }

        // Clear any existing launch timer before creating new one (prevent multiple timers)
        if (this.launchTimer) {
            console.log('[LAUNCH] Clearing existing launch timer');
            clearTimeout(this.launchTimer);
            this.launchTimer = null;
        }

        // Update text based on mode
        if (isReconnect) {
            // Reconnection mode: Show "Launching..." and auto-connect
            if (titleEl) titleEl.textContent = 'Launching...';
            if (messageEl) messageEl.textContent = 'Restoring your session...';
            if (hintEl) hintEl.style.display = 'none'; // Hide hint for reconnections
            console.log('[LAUNCH] Showing reconnection screen - auto-connecting in 2s');
        } else {
            // First-time mode: Show "claude-on-the-go" and wait for tap
            if (titleEl) titleEl.textContent = 'claude-on-the-go';
            if (messageEl) messageEl.textContent = 'Tap anywhere to connect';
            if (hintEl) {
                hintEl.textContent = 'iOS requires user interaction for WebSocket connections';
                hintEl.style.display = '';
            }
            console.log('[LAUNCH] Showing first-time screen - waiting for tap');
        }

        // Show overlay
        overlay.classList.remove('hidden');

        // Handle tap/click to connect (works in both modes)
        const handleTap = () => {
            console.log('[LAUNCH] User tapped - initiating connection');

            // Hide overlay with fade out
            overlay.classList.add('hidden');

            // NOTE: 'claude_has_connected' flag is now set in onOpen()
            // This ensures it's set on EVERY successful connection, not just tap

            // Clear auto-connect timer if exists
            if (this.launchTimer) {
                clearTimeout(this.launchTimer);
                this.launchTimer = null;
            }

            // Connect to WebSocket
            this.connect();

            // Remove event listener after first tap
            overlay.removeEventListener('click', handleTap);
        };

        // Listen for tap/click
        overlay.addEventListener('click', handleTap);

        // Auto-connect after delay for reconnections
        if (isReconnect) {
            this.launchTimer = setTimeout(() => {
                console.log('[LAUNCH] Auto-connecting after delay');
                // DON'T hide overlay here - let onMessage() hide it when first output arrives
                // This prevents black screen if Claude takes longer than 2s to produce output
                // Remove tap listener
                overlay.removeEventListener('click', handleTap);
                // Connect
                this.connect();
            }, 2000); // 2 second delay for nice animation viewing
        }
    }

    showTapToConnect() {
        // Use the new showLaunchingScreen method in first-time mode
        this.showLaunchingScreen(false);
    }

    showConnectionFailed() {
        console.log('[CIRCUIT BREAKER] Showing connection failed UI');
        this.updateStatus('Connection Failed', 'error');

        // CRITICAL: Hide all other overlays before showing error overlay
        // This prevents overlay stacking bug where multiple screens show at once
        const launchOverlay = document.getElementById('tap-to-connect');
        if (launchOverlay) {
            launchOverlay.classList.add('hidden');
            console.log('[CIRCUIT BREAKER] Hid launch overlay');
        }

        const installBanner = document.getElementById('install-banner');
        if (installBanner) {
            installBanner.classList.add('hidden');
            console.log('[CIRCUIT BREAKER] Hid PWA install banner');
        }

        const keyboardToolbar = document.getElementById('keyboard-toolbar');
        if (keyboardToolbar) {
            keyboardToolbar.classList.add('hidden');
            console.log('[CIRCUIT BREAKER] Hid keyboard toolbar');
        }

        // Show connection failed overlay
        const overlay = document.getElementById('connection-failed-overlay');
        if (!overlay) {
            console.error('[CIRCUIT BREAKER] Connection failed overlay not found in DOM');
            // Fallback: show error in terminal
            if (this.term) {
                this.term.write('\r\n\x1b[31m[Connection Failed]\x1b[0m\r\n');
                this.term.write('Too many connection failures. Please check your network and tap to retry.\r\n');
            }
            return;
        }

        // Populate diagnostics section with last error details
        if (this.lastErrorDetails) {
            const diagError = document.getElementById('diag-error');
            const diagUrl = document.getElementById('diag-url');
            const diagStatus = document.getElementById('diag-status');
            const diagHints = document.getElementById('diag-hints');

            if (diagError) {
                if (this.lastErrorDetails.type === 'close') {
                    diagError.textContent = `${this.lastErrorDetails.codeDescription} (${this.lastErrorDetails.code})`;
                } else {
                    diagError.textContent = 'Connection error (details unavailable)';
                }
            }

            if (diagUrl) {
                diagUrl.textContent = this.lastErrorDetails.url;
            }

            if (diagStatus) {
                const online = this.lastErrorDetails.online ? '✓ Online' : '✗ Offline';
                const readyState = this.lastErrorDetails.readyStateText || 'Unknown';
                diagStatus.textContent = `${online} • ${readyState}`;
            }

            if (diagHints) {
                const hints = [];

                if (!this.lastErrorDetails.online) {
                    hints.push('<strong>Device is offline</strong><ul><li>Check WiFi or mobile data connection</li></ul>');
                } else if (this.lastErrorDetails.code === 1006 || this.lastErrorDetails.readyState === 0) {
                    hints.push('<strong>Server unreachable</strong><ul>' +
                        '<li>Check server is running on your Mac</li>' +
                        '<li>Ensure both devices are on same WiFi</li>' +
                        '<li>Check firewall allows port 8000</li>' +
                        '<li>Try using IP address instead of hostname</li>' +
                        '</ul>');
                } else if (this.lastErrorDetails.code === 1011) {
                    hints.push('<strong>Server error</strong><ul>' +
                        '<li>Check backend logs for errors</li>' +
                        '<li>Server may need restart</li>' +
                        '</ul>');
                }

                diagHints.innerHTML = hints.join('') || 'Connection failed after multiple attempts';
            }
        }

        overlay.classList.remove('hidden');
        console.log('[CIRCUIT BREAKER] Connection failed overlay displayed');
        this.logDiagnostics(); // Log full diagnostics to console
    }

    async copyDiagnostics() {
        const diag = this.getDiagnostics();
        const diagnosticsText = `Claude-onTheGo Diagnostics Report
Generated: ${diag.timestamp}

Connection Details:
- URL: ${diag.url}
- State: ${diag.readyStateText} (${diag.readyState})
- Network Online: ${diag.online}
- Attempts: ${diag.connectionStatus.reconnectAttempts}
- Consecutive Failures: ${diag.connectionStatus.consecutiveFailures}
- Circuit Breaker: ${diag.connectionStatus.circuitBreakerTripped ? 'TRIPPED' : 'OK'}

Last Error:
${diag.lastError ? JSON.stringify(diag.lastError, null, 2) : 'No error recorded'}

Recent Errors:
${diag.recentErrors.map((e, i) => `${i + 1}. [${e.timestamp}] ${e.type}: ${e.codeDescription || e.error?.message || 'Unknown'}`).join('\n')}

Browser Info:
- User Agent: ${diag.browser.userAgent}
- Platform: ${diag.browser.platform}
- Language: ${diag.browser.language}

Session:
- Has Session: ${diag.session.hasSession}
- Session ID: ${diag.session.sessionId}
`;

        try {
            await navigator.clipboard.writeText(diagnosticsText);
            this.showToast('Diagnostics copied to clipboard!', 2000);
            console.log('[DIAGNOSTICS] Copied to clipboard');
        } catch (error) {
            console.error('[DIAGNOSTICS] Failed to copy:', error);
            // Fallback: show alert with text to copy manually
            alert('Could not copy automatically. Please copy manually:\n\n' + diagnosticsText);
        }
    }

    resetCircuitBreaker() {
        console.log('[CIRCUIT BREAKER] Resetting circuit breaker - manual retry');

        // Reset circuit breaker state
        this.circuitBreakerTripped = false;
        this.consecutiveFailures = 0;
        this.reconnectAttempts = 0;
        this.currentReconnectDelay = this.reconnectBaseDelay;

        // Hide connection failed overlay
        const overlay = document.getElementById('connection-failed-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }

        // Clear stale session and try fresh connection
        this.clearSessionFromStorage();
        this.sessionId = null;

        // Attempt reconnection
        this.showToast('Retrying connection...', 2000);
        this.connect();
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

    scrollToFollow() {
        // Smart scroll that follows conversation without pushing content off-screen
        // EXCEPTION: On initial load, ALWAYS scroll to bottom (don't preserve default top position)
        const viewport = document.querySelector('.xterm-viewport');
        if (!viewport || !this.term || !this.term.buffer) {
            return;
        }

        try {
            const cursorY = this.term.buffer.active.cursorY;
            const rows = this.term.rows;
            const lineHeight = this.term._core._renderService.dimensions.actualCellHeight;

            // Calculate how far user is from bottom
            const scrollBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
            const nearBottomThreshold = lineHeight * 3; // Within 3 rows of bottom

            // Check if user is near bottom
            const isNearBottom = scrollBottom <= nearBottomThreshold;

            // INITIAL LOAD: Force scroll to absolute bottom after DOM has painted
            // This ensures Claude banner is visible immediately on fresh load
            if (this.isInitialLoad) {
                // Scroll to maximum position
                viewport.scrollTop = viewport.scrollHeight;
                this.isInitialLoad = false; // Only do this once

                // Double-check after another frame (iOS Safari sometimes needs this)
                requestAnimationFrame(() => {
                    viewport.scrollTop = viewport.scrollHeight;
                    console.log(`[SCROLL] Initial load - forced scroll to bottom (scrollTop=${viewport.scrollTop}, scrollHeight=${viewport.scrollHeight})`);
                });
                return;
            }

            // NORMAL OPERATION: Only auto-scroll if user is near bottom (hasn't manually scrolled up)
            if (!isNearBottom) {
                console.log('[SCROLL] User scrolled up - preserving position');
                return;
            }

            // Scroll to show cursor + 2 rows of context below
            // This keeps cursor visible without pushing content off-screen
            const targetScrollTop = Math.max(0, (cursorY - rows + 3) * lineHeight);
            viewport.scrollTop = targetScrollTop;

            console.log(`[SCROLL] Smart scroll to cursor Y=${cursorY}, scrollTop=${viewport.scrollTop}`);
        } catch (e) {
            console.error('[SCROLL] Error in scrollToFollow:', e);
        }
    }

    scheduleSmoothScroll() {
        // Debounce scroll calls to prevent scroll-spam during rapid streaming
        if (this.scrollDebounceTimer) {
            clearTimeout(this.scrollDebounceTimer);
        }

        this.scrollDebounceTimer = setTimeout(() => {
            this.scrollToFollow();
            this.scrollDebounceTimer = null;
        }, this.scrollDebounceDelay);
    }

    logTiming(marker, description) {
        // Log timing diagnostic for connection flow analysis
        if (!this.connectionStartTime) {
            return; // Not tracking timing
        }

        const elapsed = Date.now() - this.connectionStartTime;
        const elapsedSec = (elapsed / 1000).toFixed(2);

        this.timingMarkers[marker] = {
            elapsed: elapsed,
            timestamp: Date.now(),
            description: description
        };

        console.log(`[TIMING] +${elapsedSec}s - ${marker}: ${description}`);

        // Log summary on first output
        if (marker === 'first_output') {
            console.group('[TIMING SUMMARY] Connection Flow');
            Object.keys(this.timingMarkers).forEach(key => {
                const marker = this.timingMarkers[key];
                const sec = (marker.elapsed / 1000).toFixed(2);
                console.log(`  +${sec}s - ${key}: ${marker.description}`);
            });
            console.groupEnd();
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
