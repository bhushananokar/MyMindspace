export class AudioStreamer {
  audioContext: AudioContext;
  nextPlayTime: number = 0;
  sourceNodes: AudioBufferSourceNode[] = [];

  constructor(audioContext: AudioContext) {
    this.audioContext = audioContext;
  }

  addPCM16(base64Data: string) {
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const pcm16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(pcm16.length);
    for (let i = 0; i < pcm16.length; i++) {
      float32[i] = pcm16[i] / 0x7FFF;
    }

    const audioBuffer = this.audioContext.createBuffer(1, float32.length, 24000);
    audioBuffer.getChannelData(0).set(float32);

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);

    source.onended = () => {
      this.sourceNodes = this.sourceNodes.filter(n => n !== source);
    };
    this.sourceNodes.push(source);

    if (this.nextPlayTime < this.audioContext.currentTime) {
      this.nextPlayTime = this.audioContext.currentTime;
    }
    source.start(this.nextPlayTime);
    this.nextPlayTime += audioBuffer.duration;
  }

  stop() {
    this.sourceNodes.forEach(node => {
      try { node.stop(); } catch (e) {}
    });
    this.sourceNodes = [];
    this.nextPlayTime = 0;
  }
}
