class SilenceDetectorProcessor extends AudioWorkletProcessor {
     constructor() {
         super();
         this.silenceThreshold = 0.02; // Adjust for silence sensitivity
         this.silenceDuration = 0; // Duration of silence in ms
         this.silenceTimeout = 4000; // Stop recording after 4 seconds of silence
     }
 
     process(inputs) {
         const input = inputs[0];
         if (input.length > 0) {
             const isSilent = input[0].every(sample => Math.abs(sample) < this.silenceThreshold);
             if (isSilent) {
                 this.silenceDuration += 128 / sampleRate * 1000;
                 if (this.silenceDuration >= this.silenceTimeout) {
                     this.port.postMessage("silence");
                 }
             } else {
                 this.silenceDuration = 0;
             }
         }
         return true;
     }
 }
 
 registerProcessor("silence-detector-processor", SilenceDetectorProcessor);
 