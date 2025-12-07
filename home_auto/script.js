let isStarted = false;
let homeName = '';
let currentText = '';
let systemState = 'idle';
let deviceState = {
  light: false,
  fan: false,
  pump: false,
};

let recognitionRef = null;
let synthRef = null;
let systemStateRef = 'idle';
let homeNameRef = '';
let restartTimeoutRef = null;
let permissionsGrantedRef = false;
let isListeningActiveRef = false;
let nextActionRef = null;

     let API_KEY = localStorage.getItem('API_KEY') || prompt('Enter API Key:');
     if (API_KEY) {
       localStorage.setItem('API_KEY', API_KEY);
     } else {
       alert('API Key required!');
       location.reload();
     }


const mainButton = document.getElementById('mainButton');
const currentTextContainer = document.getElementById('currentTextContainer');
const currentTextContent = document.getElementById('currentTextContent');

function updateSystemState(newState) {
  systemState = newState;
  systemStateRef = newState;

  mainButton.className = `main-button ${newState}`;
  mainButton.disabled =
    newState === 'processing' || newState === 'requesting_permissions';

  updateButtonInner();

  if (
    nextActionRef &&
    (newState === 'naming' || newState === 'ready' || newState === 'listening')
  ) {
    const action = nextActionRef;
    nextActionRef = null;
    setTimeout(action, 100);
  }
}

function updateHomeName(newName) {
  homeName = newName;
  homeNameRef = newName;
}

function updateCurrentText(newText) {
  currentText = newText;
  if (newText) {
    currentTextContainer.style.display = 'block';
    currentTextContent.innerHTML = highlightHomeName(newText);
  } else {
    currentTextContainer.style.display = 'none';
  }
}

function updateDeviceState(newState) {
  deviceState = { ...newState };
}

function updateIsStarted(newValue) {
  isStarted = newValue;

  if (newValue) {
    mainButton.onclick = handleStop;
  } else {
    mainButton.onclick = handleStart;
  }
}

function initializeSpeechSynthesis() {
  if (typeof window !== 'undefined') {
    synthRef = window.speechSynthesis;
  }
}

function cleanup() {
  isListeningActiveRef = false;
  nextActionRef = null;

  if (restartTimeoutRef) {
    clearTimeout(restartTimeoutRef);
    restartTimeoutRef = null;
  }

  if (recognitionRef) {
    try {
      recognitionRef.stop();
    } catch (e) {}
    recognitionRef = null;
  }

  if (synthRef) {
    try {
      synthRef.cancel();
    } catch (e) {}
  }
}

async function requestPermissions() {
  try {
    updateSystemState('requesting_permissions');

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 44100,
        channelCount: 1,
      },
    });

    if (synthRef) {
      const testUtterance = new SpeechSynthesisUtterance('Test');
      testUtterance.volume = 0.05;
      synthRef.speak(testUtterance);
    }

    stream.getTracks().forEach((track) => track.stop());

    permissionsGrantedRef = true;
    return true;
  } catch (error) {
    updateSystemState('idle');
    return false;
  }
}

async function speak(text, nextAction) {
  return new Promise((resolve) => {
    if (systemStateRef === 'idle') {
      resolve();
      return;
    }

    if (nextAction) {
      nextActionRef = nextAction;
    }

    if (recognitionRef) {
      recognitionRef.stop();
      recognitionRef = null;
      isListeningActiveRef = false;
    }

    updateSystemState('speaking');
    updateCurrentText(text);

    if (synthRef) {
      synthRef.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      utterance.lang = 'en-US';

      utterance.onstart = () => {};

      utterance.onend = () => {
        updateCurrentText('');

        if (systemStateRef === 'speaking') {
          if (homeNameRef) {
            updateSystemState('ready');
          } else {
            updateSystemState('naming');
          }
        }

        setTimeout(() => {
          resolve();
        }, 300);
      };

      utterance.onerror = (error) => {
        updateCurrentText('');
        updateSystemState(homeNameRef ? 'ready' : 'naming');
        resolve();
      };

      synthRef.speak(utterance);
    } else {
      updateSystemState(homeNameRef ? 'ready' : 'naming');
      resolve();
    }
  });
}

async function processCommand(command) {
  if (!command.trim() || systemStateRef === 'idle') {
    return;
  }

  updateSystemState('processing');

  try {
    const response = await fetch('https://zenova-server.onrender.com/request', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        API_KEY,
        message: command,
      }),
    });

    if (response.ok) {
      const result = await response.text();
      await executeDeviceCommands(result);
    } else {
      await speak("Sorry, I couldn't process that command", () =>
        startListening()
      );
      return;
    }
  } catch (error) {
    await speak('Sorry, connection error', () => startListening());
    return;
  }

  scheduleNextListen(1000);
}

async function executeDeviceCommands(commands) {
  if (!commands || systemStateRef === 'idle') return;

  const newState = { ...deviceState };
  const changes = [];

  for (const digit of commands) {
    switch (digit) {
      case '0':
        if (newState.light) {
          newState.light = false;
          changes.push('Light off');
        }
        break;
      case '1':
        if (!newState.light) {
          newState.light = true;
          changes.push('Light on');
        }
        break;
      case '2':
        if (newState.fan) {
          newState.fan = false;
          changes.push('Fan off');
        }
        break;
      case '3':
        if (!newState.fan) {
          newState.fan = true;
          changes.push('Fan on');
        }
        break;
      case '4':
        if (newState.pump) {
          newState.pump = false;
          changes.push('Pump off');
        }
        break;
      case '5':
        if (!newState.pump) {
          newState.pump = true;
          changes.push('Pump on');
        }
        break;
      default:
    }
  }

  updateDeviceState(newState);

  if (changes.length > 0) {
    const announcement = changes.join(', ');
    await speak(announcement, () => startListening());
  } else {
    await speak('Done', () => startListening());
  }
}

function scheduleNextListen(delay = 1000) {
  if (restartTimeoutRef) {
    clearTimeout(restartTimeoutRef);
  }

  restartTimeoutRef = setTimeout(() => {
    startListening();
  }, delay);
}

function startListening() {
  if (systemStateRef === 'idle') {
    return;
  }

  if (systemStateRef === 'speaking') {
    scheduleNextListen(500);
    return;
  }

  if (systemStateRef === 'processing') {
    scheduleNextListen(500);
    return;
  }

  if (recognitionRef || isListeningActiveRef) {
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    return;
  }

  recognitionRef = new SpeechRecognition();
  isListeningActiveRef = true;

  recognitionRef.continuous = false;
  recognitionRef.interimResults = true;
  recognitionRef.lang = 'en-US';
  recognitionRef.maxAlternatives = 5;

  const mode = systemStateRef === 'naming' ? 'naming' : 'listening';
  updateSystemState(systemStateRef === 'naming' ? 'naming' : 'listening');
  updateCurrentText('');

  recognitionRef.onstart = () => {};

  recognitionRef.onresult = async (event) => {
    if (systemStateRef === 'idle') return;

    let bestTranscript = '';
    let bestConfidence = 0;
    let isFinal = false;

    for (let i = 0; i < event.results.length; i++) {
      const result = event.results[i];
      if (result.isFinal) isFinal = true;

      for (let j = 0; j < result.length; j++) {
        const alternative = result[j];
        const transcript = alternative.transcript.trim();
        const confidence = alternative.confidence || 0.8;

        if (systemStateRef === 'naming') {
          const words = transcript.split(/\s+/);
          if (
            words.length === 1 &&
            words[0].length > 1 &&
            confidence > bestConfidence
          ) {
            bestTranscript = transcript;
            bestConfidence = confidence;
          }
        } else {
          if (confidence > bestConfidence) {
            bestTranscript = transcript;
            bestConfidence = confidence;
          }
        }
      }
    }

    if (bestTranscript && !isFinal) {
      updateCurrentText(`${bestTranscript}...`);
    }

    if (!isFinal || !bestTranscript) return;

    updateCurrentText(bestTranscript);

    if (systemStateRef === 'naming') {
      const name = bestTranscript
        .trim()
        .split(/\s+/)[0]
        .replace(/[^a-zA-Z0-9]/g, '');

      if (name && name.length > 1 && bestConfidence > 0.4) {
        updateHomeName(name);
        homeNameRef = name;

        await speak(
          `Hello, I am ${name}, your AI-powered home assistant. Ready for commands.`,
          () => startListening()
        );
      } else {
        await speak('Please say the house name clearly', () =>
          startListening()
        );
      }
      return;
    }

    if (systemStateRef === 'listening' && homeNameRef && bestConfidence > 0.5) {
      const lowerText = bestTranscript.toLowerCase();
      const lowerHomeName = homeNameRef.toLowerCase();

      const patterns = [
        lowerHomeName,
        `hey ${lowerHomeName}`,
        `hi ${lowerHomeName}`,
      ];
      let found = false;
      let command = '';

      for (const pattern of patterns) {
        if (lowerText.includes(pattern)) {
          found = true;
          const idx = lowerText.indexOf(pattern);
          command = bestTranscript.substring(idx + pattern.length).trim();
          break;
        }
      }

      if (found) {
        if (command) {
          await processCommand(command);
        } else {
          await speak('Yes?', () => startListening());
        }
      } else {
        scheduleNextListen(800);
      }
    } else {
      scheduleNextListen(800);
    }
  };

  recognitionRef.onerror = (event) => {
    recognitionRef = null;
    isListeningActiveRef = false;

    if (event.error === 'not-allowed') {
      updateSystemState('idle');
      updateIsStarted(false);
    } else if (event.error === 'no-speech') {
      scheduleNextListen(1000);
    } else {
      scheduleNextListen(2000);
    }
  };

  recognitionRef.onend = () => {
    recognitionRef = null;
    isListeningActiveRef = false;

    if (systemStateRef === 'listening' || systemStateRef === 'naming') {
      scheduleNextListen(1000);
    }
  };

  try {
    recognitionRef.start();
  } catch (error) {
    recognitionRef = null;
    isListeningActiveRef = false;
    scheduleNextListen(2000);
  }
}

async function handleStart() {
  if (isStarted) return;

  const hasPermissions = await requestPermissions();
  if (!hasPermissions) {
    return;
  }

  updateIsStarted(true);

  await speak('Name the house', () => {
    startListening();
  });
}

function handleStop() {
  updateIsStarted(false);
  updateSystemState('idle');
  updateCurrentText('');
  updateHomeName('');
  homeNameRef = '';
  permissionsGrantedRef = false;
  isListeningActiveRef = false;
  nextActionRef = null;

  cleanup();
}

function highlightHomeName(text) {
  if (!homeName || !text) return text;

  const regex = new RegExp(`\\b(${homeName})\\b`, 'gi');
  const parts = text.split(regex);

  return parts
    .map((part, index) =>
      part.toLowerCase() === homeName.toLowerCase()
        ? `<span class="home-name-highlight">${part}</span>`
        : part
    )
    .join('');
}

function updateButtonInner() {
  const buttonInner = mainButton.querySelector('.button-inner');

  if (isStarted) {
    buttonInner.innerHTML = `<div class="status-square ${systemState}"></div>`;
  } else {
    buttonInner.innerHTML = '<div class="play-icon"></div>';
  }
}

function initializeApp() {
  mainButton.onclick = handleStart;

  initializeSpeechSynthesis();

  mainButton.disabled =
    systemState === 'processing' || systemState === 'requesting_permissions';
  updateButtonInner();

  window.addEventListener('beforeunload', cleanup);

  setTimeout(() => {
    console.log('Auto-starting voice assistant...');
    handleStart();
  }, 2000);
}

document.addEventListener('DOMContentLoaded', initializeApp);
