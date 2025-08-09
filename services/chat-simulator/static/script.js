class ChatSimulatorUI {
    constructor() {
        this.ws = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.selectedMessageType = 'normal';
        this.stats = {
            total: 0,
            approved: 0,
            flagged: 0,
            filtered: 0,
            processingTimes: []
        };
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkAudioSupport();
        this.connectWebSocket();
    }

    initializeElements() {
        // Control buttons
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.sendBtn = document.getElementById('sendBtn');
        this.sendSingleBtn = document.getElementById('sendSingleBtn');
        this.recordBtn = document.getElementById('recordBtn');

        // Input elements
        this.messageInput = document.getElementById('messageInput');
        this.chatContainer = document.getElementById('chatContainer');
        this.audioVisualizer = document.getElementById('audioVisualizer');

        // Status elements
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.wsStatus = document.getElementById('wsStatus');
        this.simStatus = document.getElementById('simStatus');
        this.audioStatus = document.getElementById('audioStatus');

        // Stats elements
        this.totalMessages = document.getElementById('totalMessages');
        this.approvedMessages = document.getElementById('approvedMessages');
        this.flaggedMessages = document.getElementById('flaggedMessages');
        this.avgProcessingTime = document.getElementById('avgProcessingTime');

        // Message type buttons
        this.typeButtons = document.querySelectorAll('.type-btn');
    }

    setupEventListeners() {
        // Control buttons
        this.startBtn.addEventListener('click', () => this.startSimulation());
        this.stopBtn.addEventListener('click', () => this.stopSimulation());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.sendSingleBtn.addEventListener('click', () => this.sendSingleMessage());
        this.recordBtn.addEventListener('click', () => this.toggleRecording());

        // Input handling
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Message type selection
        this.typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.typeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedMessageType = btn.dataset.type;
            });
        });

        // Auto-scroll chat container
        this.chatContainer.addEventListener('scroll', () => {
            const { scrollTop, scrollHeight, clientHeight } = this.chatContainer;
            const isScrolledToBottom = scrollTop + clientHeight >= scrollHeight - 5;
            this.chatContainer.dataset.autoScroll = isScrolledToBottom;
        });
    }

    async checkAudioSupport() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            this.audioStatus.textContent = 'Available';
            this.audioStatus.style.color = '#51cf66';
        } catch (error) {
            this.audioStatus.textContent = 'Not Available';
            this.audioStatus.style.color = '#ff6b6b';
            this.recordBtn.disabled = true;
            this.recordBtn.title = 'Microphone access denied or not available';
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.updateConnectionStatus(true);
                console.log('WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onclose = () => {
                this.updateConnectionStatus(false);
                console.log('WebSocket disconnected');
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected) {
        if (connected) {
            this.statusIndicator.classList.add('connected');
            this.statusText.textContent = 'Connected';
            this.wsStatus.textContent = 'Connected';
            this.wsStatus.style.color = '#51cf66';
        } else {
            this.statusIndicator.classList.remove('connected');
            this.statusText.textContent = 'Disconnected';
            this.wsStatus.textContent = 'Disconnected';
            this.wsStatus.style.color = '#ff6b6b';
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'chat_message') {
            this.displayMessage(data);
            this.updateStats(data);
        }
    }

    displayMessage(data) {
        const { message, moderation_result, filter_result, processing_time_ms } = data;
        
        // Determine message status
        let status = 'approved';
        let decision = 'Approved';
        
        if (!filter_result?.should_process) {
            status = 'filtered';
            decision = 'Filtered';
        } else if (moderation_result) {
            // Check for various toxic/harmful decisions
            const toxicDecisions = ['Flagged', 'Block', 'Toxic', 'Spam', 'PII', 'Harmful', 'Inappropriate'];
            if (toxicDecisions.includes(moderation_result.decision)) {
                status = 'flagged';
                decision = moderation_result.decision;
            }
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${status}`;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        const confidence = moderation_result?.confidence ? 
            `${(moderation_result.confidence * 100).toFixed(1)}%` : 'N/A';
        
        messageElement.innerHTML = `
            <div class="message-header">
                <div class="user-info">
                    <span class="username">${this.escapeHtml(message.username)}</span>
                    <span class="channel">#${message.channel_id}</span>
                </div>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message.message)}</div>
            <div class="moderation-result">
                <span class="decision ${status}">${decision}</span>
                <span class="confidence">Confidence: ${confidence}</span>
                <span class="processing-time">${processing_time_ms.toFixed(1)}ms</span>
            </div>
            ${moderation_result?.reasoning ? `
                <div class="reasoning">
                    <strong>Reasoning:</strong> ${this.escapeHtml(moderation_result.reasoning)}
                </div>
            ` : ''}
        `;

        this.chatContainer.appendChild(messageElement);
        
        // Auto-scroll if user is at bottom
        if (this.chatContainer.dataset.autoScroll !== 'false') {
            this.scrollToBottom();
        }

        // Animate new message
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(20px)';
        setTimeout(() => {
            messageElement.style.transition = 'all 0.3s ease';
            messageElement.style.opacity = '1';
            messageElement.style.transform = 'translateY(0)';
        }, 10);
    }

    updateStats(data) {
        this.stats.total++;
        this.stats.processingTimes.push(data.processing_time_ms);

        if (!data.filter_result?.should_process) {
            this.stats.filtered++;
        } else if (data.moderation_result) {
            // Check for various toxic/harmful decisions
            const toxicDecisions = ['Flagged', 'Block', 'Toxic', 'Spam', 'PII', 'Harmful', 'Inappropriate'];
            if (toxicDecisions.includes(data.moderation_result.decision)) {
                this.stats.flagged++;
            } else {
                this.stats.approved++;
            }
        } else {
            this.stats.approved++;
        }

        // Update UI
        this.totalMessages.textContent = this.stats.total;
        this.approvedMessages.textContent = this.stats.approved;
        this.flaggedMessages.textContent = this.stats.flagged;
        
        const avgTime = this.stats.processingTimes.reduce((a, b) => a + b, 0) / this.stats.processingTimes.length;
        this.avgProcessingTime.textContent = `${avgTime.toFixed(1)}ms`;
    }

    async startSimulation() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'start_simulation' }));
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.simStatus.textContent = 'Running';
            this.simStatus.style.color = '#51cf66';
        } else {
            this.showNotification('WebSocket not connected', 'error');
        }
    }

    async stopSimulation() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'stop_simulation' }));
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.simStatus.textContent = 'Stopped';
            this.simStatus.style.color = '#ff6b6b';
        }
    }

    clearChat() {
        this.chatContainer.innerHTML = `
            <div style="text-align: center; color: #718096; padding: 40px;">
                <i class="fas fa-comments" style="font-size: 3em; margin-bottom: 20px; opacity: 0.3;"></i>
                <p>Chat messages will appear here...</p>
                <p style="font-size: 14px; margin-top: 10px;">Start the simulation or send a message to begin</p>
            </div>
        `;
        
        // Reset stats
        this.stats = {
            total: 0,
            approved: 0,
            flagged: 0,
            filtered: 0,
            processingTimes: []
        };
        
        this.totalMessages.textContent = '0';
        this.approvedMessages.textContent = '0';
        this.flaggedMessages.textContent = '0';
        this.avgProcessingTime.textContent = '0ms';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        try {
            const response = await fetch('/api/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: 'user_web',
                    username: 'WebUser',
                    channel_id: 'web-chat'
                })
            });

            if (response.ok) {
                this.messageInput.value = '';
                this.showNotification('Message sent successfully', 'success');
            } else {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showNotification('Failed to send message', 'error');
        }
    }

    async sendSingleMessage() {
        try {
            const response = await fetch(`/simulate/single?message_type=${this.selectedMessageType}`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.displayMessage({
                    message: data.message,
                    moderation_result: data.moderation_result,
                    filter_result: data.filter_result,
                    processing_time_ms: 0 // Single messages don't have processing time in response
                });
                this.showNotification(`${this.selectedMessageType} message sent`, 'success');
            } else {
                throw new Error('Failed to send test message');
            }
        } catch (error) {
            console.error('Error sending test message:', error);
            this.showNotification('Failed to send test message', 'error');
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                }
            });

            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.audioChunks = [];
            this.isRecording = true;

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processAudioRecording();
            };

            this.mediaRecorder.start(100); // Collect data every 100ms
            
            // Update UI
            this.recordBtn.classList.add('recording');
            this.recordBtn.innerHTML = '<i class="fas fa-stop"></i>';
            this.audioVisualizer.style.display = 'flex';
            this.audioVisualizer.classList.add('active');
            
            this.showNotification('Recording started...', 'info');

        } catch (error) {
            console.error('Error starting recording:', error);
            this.showNotification('Failed to start recording', 'error');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            this.isRecording = false;
            this.recordBtn.classList.remove('recording');
            this.recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            this.audioVisualizer.style.display = 'none';
            this.audioVisualizer.classList.remove('active');
        }
    }

    async processAudioRecording() {
        if (this.audioChunks.length === 0) return;

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        
        // For now, we'll simulate audio processing
        // In a real implementation, you would send this to a speech-to-text service
        this.showNotification('Audio processing not implemented yet', 'info');
        
        // Simulate converting audio to text
        const simulatedText = "This is a simulated transcription of the audio message.";
        this.messageInput.value = simulatedText;
        
        this.showNotification('Audio transcribed (simulated)', 'success');
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;

        // Set background color based on type
        const colors = {
            success: '#51cf66',
            error: '#ff6b6b',
            info: '#4299e1',
            warning: '#ffd43b'
        };
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatSimulatorUI();
});
