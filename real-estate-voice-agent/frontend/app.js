/* ──────────────────────────────────────────────────────────
   Real Estate Voice Agent Platform - Client Application Controller
   ────────────────────────────────────────────────────────── */

// ── DOM State Variables ──
let activeSessionId = null;
let activeLeadId = null;
let activePhone = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let activeAudio = null;

// ── VAD State Variables ──
let localStream = null;
let audioContext = null;
let analyser = null;
let microphone = null;
let vadInterval = null;
let speechDetected = false;
let isAgentSpeaking = false;
const SPEAKING_THRESHOLD = 3.0; // Responsive threshold for time-domain absolute deviation
const SILENCE_DURATION = 1500; // 1.5 seconds of silence

// ── DOM Element Selectors ──
const leadForm = document.getElementById('lead-form');
const saveLeadBtn = document.getElementById('save-lead-btn');
const startCallBtn = document.getElementById('start-call-btn');
const endCallBtn = document.getElementById('end-call-btn');
const micBtn = document.getElementById('mic-btn');
const micStatusLabel = document.getElementById('mic-status-label');
const chatTranscriptBox = document.getElementById('chat-transcript-box');
const currentPhaseBadge = document.getElementById('current-phase-badge');
const currentLangBadge = document.getElementById('current-lang-badge');

const chatInputBox = document.getElementById('chat-input-box');
const chatTextField = document.getElementById('chat-text-field');
const chatSendBtn = document.getElementById('chat-send-btn');

const summaryBodyBox = document.getElementById('summary-body-box');
const fetchSummaryBtn = document.getElementById('fetch-summary-btn');

const siteVisitTag = document.getElementById('site-visit-tag');
const followUpTag = document.getElementById('follow-up-tag');
const manualDateInput = document.getElementById('manual-date');
const manualTimeInput = document.getElementById('manual-time');
const manualVisitBtn = document.getElementById('manual-visit-btn');
const manualFollowupBtn = document.getElementById('manual-followup-btn');

// ── Lead Save handler ──
leadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const name = document.getElementById('lead-name').value;
  const phone = document.getElementById('lead-phone').value;
  const email = document.getElementById('lead-email').value;
  const source = document.getElementById('lead-source').value;

  try {
    const res = await fetch('/api/create-lead', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, phone, email, source })
    });
    
    if (!res.ok) {
      const err = await res.json();
      alert(`Registration failed: ${err.detail || 'check parameters'}`);
      return;
    }
    
    const data = await res.json();
    activeLeadId = data.id;
    activePhone = data.phone;
    
    alert(`Lead registered successfully! Click "Start Conversation" to call ${data.name}.`);
    
    // Enable call start
    startCallBtn.removeAttribute('disabled');
    startCallBtn.classList.remove('disabled');
  } catch (error) {
    console.error('Error registering lead:', error);
    alert('Failed to connect to API server.');
  }
});

// ── Start Conversation ──
startCallBtn.addEventListener('click', async () => {
  if (!activePhone) return;

  // Request mic permission and stream first
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    console.error("Mic access denied:", err);
    appendSystemLog("Microphone access is required for automatic voice agents.");
    alert("Microphone permission is required to use this voice agent.");
    startCallBtn.removeAttribute('disabled');
    startCallBtn.classList.remove('disabled');
    return;
  }

  appendSystemLog("Initiating outbound call connection...");
  startCallBtn.classList.add('disabled');
  startCallBtn.setAttribute('disabled', 'true');

  try {
    const res = await fetch('/api/start-conversation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: activePhone })
    });

    if (!res.ok) {
      appendSystemLog("Call connection failed.");
      startCallBtn.removeAttribute('disabled');
      startCallBtn.classList.remove('disabled');
      return;
    }

    const data = await res.json();
    activeSessionId = data.session_id;

    // UI Updates
    startCallBtn.classList.add('hidden');
    endCallBtn.classList.remove('hidden');
    
    currentPhaseBadge.classList.remove('hidden');
    currentPhaseBadge.textContent = "Phase: Greeting";
    
    currentLangBadge.classList.remove('hidden');
    currentLangBadge.textContent = "Language: Gujarati";

    micBtn.classList.remove('disabled');
    micBtn.removeAttribute('disabled');
    micStatusLabel.textContent = "Listening... Speak now";
    
    chatInputBox.classList.remove('hidden');

    manualVisitBtn.classList.remove('disabled');
    manualVisitBtn.removeAttribute('disabled');
    manualFollowupBtn.classList.remove('disabled');
    manualFollowupBtn.removeAttribute('disabled');

    // Display greeting text and play speech audio
    appendChatBubble("Sarah", data.agent_text, "agent");
    if (data.agent_audio_base64) {
      playAudioPayload(data.agent_audio_base64);
    } else {
      isAgentSpeaking = false;
      startRecordingVAD();
    }
  } catch (error) {
    console.error("Error starting conversation:", error);
    appendSystemLog("Failed to reach voice agent service.");
  }
});

// ── End / Disconnect call ──
endCallBtn.addEventListener('click', () => {
  disconnectCall();
});

function disconnectCall() {
  isAgentSpeaking = false;
  stopListening();

  if (localStream) {
    localStream.getTracks().forEach(track => track.stop());
    localStream = null;
  }
  if (audioContext) {
    try {
      audioContext.close();
    } catch(e){}
    audioContext = null;
  }

  if (activeAudio) {
    activeAudio.pause();
    activeAudio = null;
  }
  
  appendSystemLog("Outbound call disconnected.");
  
  // UI Resets
  endCallBtn.classList.add('hidden');
  startCallBtn.classList.remove('hidden');
  startCallBtn.removeAttribute('disabled');
  startCallBtn.classList.remove('disabled');

  micBtn.classList.add('disabled');
  micBtn.setAttribute('disabled', 'true');
  micBtn.classList.remove('recording');
  micStatusLabel.textContent = "Input Disabled";
  
  chatInputBox.classList.add('hidden');

  manualVisitBtn.classList.add('disabled');
  manualVisitBtn.setAttribute('disabled', 'true');
  manualFollowupBtn.classList.add('disabled');
  manualFollowupBtn.setAttribute('disabled', 'true');

  if (activeSessionId) {
    fetchSummaryBtn.classList.remove('hidden');
    syncSummaryData();
  }
}

// ── VAD (Voice Activity Detection) continuous listening engine ──
function startRecordingVAD() {
  if (!localStream) return;
  if (isRecording) return;
  if (isAgentSpeaking) return;

  audioChunks = [];
  try {
    mediaRecorder = new MediaRecorder(localStream);
  } catch (err) {
    console.error("Failed to initialize MediaRecorder:", err);
    return;
  }

  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };

  mediaRecorder.onstop = async () => {
    isRecording = false;
    micBtn.classList.remove('recording');

    // Only send payload if voice was actually detected
    if (speechDetected && audioChunks.length > 0) {
      micStatusLabel.textContent = "Processing & sending speech...";
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = () => {
        const base64Data = reader.result;
        sendChatPayload({ user_audio_base64: base64Data });
      };
    } else {
      // If no speech detected, restart listening loop
      micStatusLabel.textContent = "Listening... Speak now";
      if (!isAgentSpeaking && activeSessionId) {
        setTimeout(() => {
          startRecordingVAD();
        }, 300);
      }
    }
  };

  try {
    // Initialize Web Audio API components once
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      microphone = audioContext.createMediaStreamSource(localStream);
      microphone.connect(analyser);
    }

    speechDetected = false;
    let silenceStart = null;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    micBtn.classList.add('recording');
    micStatusLabel.textContent = "Listening... Speak now";
    
    mediaRecorder.start();
    isRecording = true;

    // Periodically poll time-domain data for VAD
    if (vadInterval) clearInterval(vadInterval);
    vadInterval = setInterval(() => {
      if (!isRecording) {
        clearInterval(vadInterval);
        return;
      }

      analyser.getByteTimeDomainData(dataArray);

      // Calculate absolute deviation from the center line (128) for volume
      let totalDeviation = 0;
      for (let i = 0; i < bufferLength; i++) {
        totalDeviation += Math.abs(dataArray[i] - 128);
      }
      const averageVolume = totalDeviation / bufferLength;

      // Debug log volume to console to trace noise floors
      console.log("VAD Volume:", averageVolume.toFixed(2), "Threshold:", SPEAKING_THRESHOLD);

      if (averageVolume > SPEAKING_THRESHOLD) {
        if (!speechDetected) {
          speechDetected = true;
          micStatusLabel.textContent = "Speaking...";
        }
        silenceStart = null; // reset silence counter when active speech is heard
      } else {
        if (speechDetected) {
          if (!silenceStart) {
            silenceStart = Date.now();
          } else if (Date.now() - silenceStart > SILENCE_DURATION) {
            // User finished speaking, stop and send
            micStatusLabel.textContent = "Processing speech...";
            clearInterval(vadInterval);
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
              mediaRecorder.stop();
            }
          }
        }
      }
    }, 50);

  } catch (e) {
    console.error("Error setting up VAD Analyser:", e);
  }
}

function stopListening() {
  if (vadInterval) {
    clearInterval(vadInterval);
    vadInterval = null;
  }
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    // Avoid sending current chunk on forced stop (e.g. agent interrupt or disconnect)
    speechDetected = false;
    mediaRecorder.stop();
  }
  isRecording = false;
  if (micBtn) {
    micBtn.classList.remove('recording');
  }
}

// ── Microphone audio manual trigger/force-send ──
micBtn.addEventListener('click', () => {
  if (micBtn.classList.contains('disabled')) return;

  if (activeAudio && !activeAudio.paused) {
    // Barge-in: Stop playing agent audio and start recording immediately
    activeAudio.pause();
    activeAudio.currentTime = 0;
    isAgentSpeaking = false;
    startRecordingVAD();
  } else if (isRecording && mediaRecorder && mediaRecorder.state !== "inactive") {
    // Force stop recording and trigger send immediately (manual bypass)
    speechDetected = true;
    mediaRecorder.stop();
  } else {
    // Manually force start listening if idle
    isAgentSpeaking = false;
    startRecordingVAD();
  }
});

// ── Send chat fallback text input ──
chatSendBtn.addEventListener('click', () => {
  submitTextTurn();
});

chatTextField.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    submitTextTurn();
  }
});

function submitTextTurn() {
  const text = chatTextField.value.trim();
  if (!text) return;
  
  // Stop listening while we process text input
  stopListening();

  // Barge-in: Stop any currently playing agent audio when user submits text
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
  }
  
  chatTextField.value = '';
  appendChatBubble("You", text, "user");
  sendChatPayload({ user_text: text });
}

// ── Post dialogue package ──
async function sendChatPayload(payload) {
  if (!activeSessionId) return;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: activeSessionId,
        ...payload
      })
    });

    if (!res.ok) {
      appendSystemLog("Server failed to respond.");
      return;
    }

    const data = await res.json();
    
    // Show the customer's transcribed speech as a chat bubble
    if (data.user_text && data.user_text.trim()) {
      appendChatBubble("You", data.user_text, "user");
    }

    // Append agent reply bubble
    appendChatBubble("Sarah", data.agent_text, "agent");

    // Badges update
    currentPhaseBadge.textContent = `Phase: ${data.current_node}`;
    currentLangBadge.textContent = `Language: ${data.language}`;

    // Play audio voice response — VAD auto-restarts when agent audio ends
    if (data.agent_audio_base64) {
      micStatusLabel.textContent = "Agent responding...";
      playAudioPayload(data.agent_audio_base64);
    } else {
      isAgentSpeaking = false;
      startRecordingVAD();
    }

    // If call ended in nodes
    if (data.current_node === 'summary' || data.current_node === 'end') {
      appendSystemLog("Sarah wrapped up the call. Disconnecting...");
      setTimeout(() => {
        disconnectCall();
      }, 3000);
    }
  } catch (error) {
    console.error("Chat turn failed:", error);
    appendSystemLog("Error connection offline.");
  }
}

// ── Manual Overrides ──
manualVisitBtn.addEventListener('click', async () => {
  const date = manualDateInput.value.trim();
  const time = manualTimeInput.value.trim();
  if (!date || !time) {
    alert("Please fill manual date and time input values first.");
    return;
  }
  
  try {
    const res = await fetch('/api/book-visit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: activeSessionId, date, time })
    });
    if (res.ok) {
      siteVisitTag.textContent = `BOOKED: ${date} @ ${time}`;
      siteVisitTag.classList.add('confirmed');
    }
  } catch (e) {
    console.error(e);
  }
});

manualFollowupBtn.addEventListener('click', async () => {
  const date = manualDateInput.value.trim();
  const time = manualTimeInput.value.trim();
  if (!date || !time) {
    alert("Please fill manual date and time input values first.");
    return;
  }
  
  try {
    const res = await fetch('/api/follow-up', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: activeSessionId, date, time })
    });
    if (res.ok) {
      followUpTag.textContent = `SCHEDULED: ${date} @ ${time}`;
      followUpTag.classList.add('confirmed');
    }
  } catch (e) {
    console.error(e);
  }
});

// ── Sync Lead summary from server ──
fetchSummaryBtn.addEventListener('click', () => {
  syncSummaryData();
});

async function syncSummaryData() {
  if (!activeSessionId) return;

  try {
    const res = await fetch(`/api/summary?session_id=${activeSessionId}`);
    if (!res.ok) return;

    const data = await res.json();
    
    // Update direct booking statuses if set
    if (data.booking_status === 'booked') {
      siteVisitTag.textContent = "CONFIRMED VISITING";
      siteVisitTag.classList.add('confirmed');
    } else if (data.booking_status === 'follow_up') {
      followUpTag.textContent = "CALLBACK REQUESTED";
      followUpTag.classList.add('confirmed');
    }

    // Format and render summary template
    const questionsHTML = data.questions_asked.map(q => `<span class="pill">${q}</span>`).join('');
    const objectionsHTML = data.objections.map(o => `<span class="pill negative">${o}</span>`).join('');

    summaryBodyBox.innerHTML = `
      <div class="summary-details">
        <div class="score-card">
          <div class="score-text">
            <h3>Buyer Intent Score</h3>
            <p>Calculated based on conversation patterns</p>
          </div>
          <div class="score-badge">${data.lead_score}</div>
        </div>

        <div class="summary-row-grid">
          <div class="summary-item">
            <label>Budget</label>
            <span>${data.budget || 'Not specified'}</span>
          </div>
          <div class="summary-item">
            <label>Preferred Location</label>
            <span>${data.preferred_location || 'Not specified'}</span>
          </div>
          <div class="summary-item">
            <label>BHK Config</label>
            <span>${data.property_type || 'Not specified'}</span>
          </div>
          <div class="summary-item">
            <label>Purchase Purpose</label>
            <span>${data.purpose || 'Not specified'}</span>
          </div>
        </div>

        <div class="summary-item">
          <label>Purchase Timeline</label>
          <span>${data.timeline || 'Not specified'}</span>
        </div>

        <div class="summary-block">
          <label>Questions Asked by Lead</label>
          <div class="pill-list">${questionsHTML || '<span class="pill">None</span>'}</div>
        </div>

        <div class="summary-block">
          <label>Objections Raised</label>
          <div class="pill-list">${objectionsHTML || '<span class="pill">None</span>'}</div>
        </div>

        <div class="summary-block">
          <label>Overview Summary</label>
          <p>${data.summary_text || 'No summary text compiled.'}</p>
        </div>
      </div>
    `;
  } catch (error) {
    console.error("Summary fetch error:", error);
  }
}

// ── Audio player helpers ──
function playAudioPayload(base64Data) {
  try {
    if (activeAudio) {
      activeAudio.pause();
    }
    
    // Check base64 pattern and append prefix if missing
    let audioSrc = base64Data;
    if (!audioSrc.startsWith("data:")) {
      audioSrc = "data:audio/wav;base64," + base64Data;
    }
    
    // Set Agent Speaking state and turn off listening
    isAgentSpeaking = true;
    stopListening();
    micStatusLabel.textContent = "Agent speaking...";

    activeAudio = new Audio(audioSrc);
    
    activeAudio.addEventListener('ended', () => {
      isAgentSpeaking = false;
      micStatusLabel.textContent = "Listening... Speak now";
      startRecordingVAD();
    });

    activeAudio.play().catch(e => {
      console.warn("Audio autoplay blocked by browser policy. User gesture required.", e);
      isAgentSpeaking = false;
      micStatusLabel.textContent = "Listening... Speak now";
      startRecordingVAD();
    });
  } catch (err) {
    console.error("Failed to play audio:", err);
    isAgentSpeaking = false;
    startRecordingVAD();
  }
}

// ── Log and Transcript Appends ──
function appendChatBubble(speaker, text, speakerClass) {
  const bubble = document.createElement('div');
  bubble.className = `dialogue-turn ${speakerClass}`;
  
  const label = document.createElement('div');
  label.className = 'speaker-label';
  label.textContent = speaker;
  
  const content = document.createElement('div');
  content.textContent = text;
  
  bubble.appendChild(label);
  bubble.appendChild(content);
  
  chatTranscriptBox.appendChild(bubble);
  scrollToBottom();
}

function appendSystemLog(message) {
  const log = document.createElement('div');
  log.className = 'system-message';
  log.innerHTML = `<i class="fa-solid fa-circle-info"></i> <span>${message}</span>`;
  chatTranscriptBox.appendChild(log);
  scrollToBottom();
}

function scrollToBottom() {
  chatTranscriptBox.scrollTop = chatTranscriptBox.scrollHeight;
}
