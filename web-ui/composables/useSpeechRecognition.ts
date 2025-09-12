// web-ui/composables/useSpeechRecognition.ts
import { ref, onUnmounted } from 'vue';

// 为浏览器API添加明确的接口定义
interface SpeechRecognitionResult {
  isFinal: boolean;
  [key: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [key: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

// 定义 SpeechRecognition 构造函数的接口
interface SpeechRecognitionStatic {
  new(): SpeechRecognition;
}

// 定义 SpeechRecognition 实例的接口
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: () => void;
  onend: () => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onresult: (event: SpeechRecognitionEvent) => void;
}

declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionStatic;
    webkitSpeechRecognition: SpeechRecognitionStatic;
  }
}

interface SpeechRecognitionOptions {
  onResult?: (result: string) => void;
  onError?: (error: string) => void;
}

export function useSpeechRecognition(options: SpeechRecognitionOptions = {}) {
  const isListening = ref(false);
  const transcript = ref('');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    const errorMsg = '您的浏览器不支持语音识别功能。';
    console.error(errorMsg);
    if (options.onError) options.onError(errorMsg);
    return { isListening, transcript, start: () => {}, stop: () => {} };
  }
  
  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'zh-CN';

  recognition.onstart = () => {
    isListening.value = true;
  };

  recognition.onend = () => {
    isListening.value = false;
  };

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    console.error('Speech recognition error:', event.error);
    if (options.onError) options.onError(event.error);
    isListening.value = false;
  };

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i] && event.results[i]!.isFinal) {
            finalTranscript += event.results[i]![0]!.transcript;
        }
    }
    transcript.value = finalTranscript;
    if (options.onResult) options.onResult(finalTranscript);
  };
  
  const start = () => {
    if (!isListening.value) {
      transcript.value = '';
      recognition.start();
    }
  };

  const stop = () => {
    if (isListening.value) {
      recognition.stop();
    }
  };
  
  onUnmounted(() => {
    recognition.abort();
  });

  return {
    isListening,
    transcript,
    start,
    stop,
  };
}