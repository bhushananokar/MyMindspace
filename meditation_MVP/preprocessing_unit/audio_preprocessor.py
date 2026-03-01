import argparse
import os
from pathlib import Path
from typing import Tuple
import numpy as np
try:
    import librosa
    import librosa.display  # noqa: F401
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "librosa is required. Install with: pip install librosa soundfile matplotlib numpy"
    ) from e
try:
    import soundfile as sf
except Exception:
    sf = None  # optional, librosa can load audio via audioread
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None  # spectrogram image saving becomes optional

def load_audio(path: Path, target_sr: int) -> Tuple[np.ndarray, int]:
    y, sr = librosa.load(str(path), sr=target_sr, mono=True)
    return y, sr

def reduce_noise_simple(y: np.ndarray, sr: int, noise_ms: int = 300) -> np.ndarray:
    """
    Very simple spectral gating using a noise profile estimated from the first noise_ms.
    This is lightweight and dependency-free; for production, prefer specialized libraries.
    """
    noise_frames = int(sr * noise_ms / 1000.0)
    noise_profile = y[:noise_frames]
    
    # Compute power spectrum
    stft = librosa.stft(y)
    magnitude = np.abs(stft)
    phase = np.angle(stft)
    
    # Estimate noise floor
    noise_stft = librosa.stft(noise_profile)
    noise_mag = np.abs(noise_stft)
    noise_floor = np.mean(noise_mag, axis=1, keepdims=True)
    
    # Simple spectral gating
    gate_threshold = noise_floor * 2.0  # 6dB above noise floor
    mask = magnitude > gate_threshold
    
    # Apply mask
    magnitude_clean = magnitude * mask
    stft_clean = magnitude_clean * np.exp(1j * phase)
    
    # Convert back to time domain
    y_clean = librosa.istft(stft_clean)
    return y_clean

def compute_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 13) -> np.ndarray:
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc.T  # transpose to [frames, n_mfcc]

def compute_mel_spectrogram(y: np.ndarray, sr: int, n_mels: int = 80) -> np.ndarray:
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    return mel_spec_db.T  # transpose to [frames, n_mels]

def save_spectrogram_png(S_db: np.ndarray, out_path: Path) -> None:
    if plt is None:
        return
    
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S_db.T, y_axis='mel', x_axis='time')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel-frequency spectrogram')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()

def process_file(
    input_path: Path,
    output_dir: Path,
    target_sr: int = 22050,
    n_mfcc: int = 13,
    n_mels: int = 80,
    reduce_noise: bool = True,
    save_spectrogram: bool = False
) -> None:
    """Process a single audio file"""
    
    # Load audio
    y, sr = load_audio(input_path, target_sr)
    
    # Reduce noise if requested
    if reduce_noise:
        y = reduce_noise_simple(y, sr)
    
    # Compute features
    mfcc = compute_mfcc(y, sr, n_mfcc)
    mel_spec = compute_mel_spectrogram(y, sr, n_mels)
    
    # Save features
    base_name = input_path.stem
    np.save(output_dir / f"{base_name}_mfcc.npy", mfcc)
    np.save(output_dir / f"{base_name}_mel.npy", mel_spec)
    
    # Save spectrogram image if requested
    if save_spectrogram:
        save_spectrogram_png(mel_spec, output_dir / f"{base_name}_spectrogram.png")

def main() -> None:
    parser = argparse.ArgumentParser(description="Audio Preprocessor")
    parser.add_argument("--input", type=str, required=True, help="Input audio file or directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--target-sr", type=int, default=22050, help="Target sample rate")
    parser.add_argument("--n-mfcc", type=int, default=13, help="Number of MFCC coefficients")
    parser.add_argument("--n-mels", type=int, default=80, help="Number of mel bins")
    parser.add_argument("--no-noise-reduction", action="store_true", help="Skip noise reduction")
    parser.add_argument("--save-spectrogram", action="store_true", help="Save spectrogram images")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        process_file(
            input_path=input_path,
            output_dir=output_dir,
            target_sr=args.target_sr,
            n_mfcc=args.n_mfcc,
            n_mels=args.n_mels,
            reduce_noise=not args.no_noise_reduction,
            save_spectrogram=args.save_spectrogram
        )
    else:
        # Process all audio files in directory
        for ext in ['*.wav', '*.mp3', '*.flac', '*.m4a']:
            for audio_file in input_path.glob(ext):
                try:
                    process_file(
                        input_path=audio_file,
                        output_dir=output_dir,
                        target_sr=args.target_sr,
                        n_mfcc=args.n_mfcc,
                        n_mels=args.n_mels,
                        reduce_noise=not args.no_noise_reduction,
                        save_spectrogram=args.save_spectrogram
                    )
                    print(f"Processed: {audio_file}")
                except Exception as e:
                    print(f"Error processing {audio_file}: {e}")


class AudioPreprocessor:
    """
    Class wrapper around existing audio preprocessing functions
    """
    
    def __init__(self, target_sr: int = 22050, n_mfcc: int = 20):
        self.target_sr = target_sr
        self.n_mfcc = n_mfcc
    
    def process_file(self, input_path, output_dir):
        """
        Process audio file using existing process_file function
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory to save processed outputs
        """
        from pathlib import Path
        
        # Convert to Path objects if needed
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use the existing process_file function
        process_file(
            input_path=input_path,
            output_dir=output_dir,
            target_sr=self.target_sr,
            n_mfcc=self.n_mfcc,
            reduce_noise=True,
            save_spectrogram=False  # Don't need images for MVP
        )


if __name__ == "__main__":
    main()