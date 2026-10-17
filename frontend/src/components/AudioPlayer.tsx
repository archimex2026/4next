'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  Play, Pause, RotateCcw, RotateCw, Volume2, VolumeX, 
  Headphones, Download, Globe, Sparkles, RefreshCw, Check,
  Sliders, Mic
} from 'lucide-react';
import { getMediaUrl, getLessonExportUrl, generateLessonAudio } from '@/lib/api';

interface AudioPlayerProps {
  audioUrl?: string;
  title: string;
  lessonId?: string;
  lessonNumber?: number;
  currentLang?: 'ro' | 'en';
  onLanguageChange?: (lang: 'ro' | 'en') => void;
  onAudioRegenerated?: (newAudioUrl: string, durationSec: number) => void;
}

export default function AudioPlayer({ 
  audioUrl, 
  title, 
  lessonId,
  lessonNumber,
  currentLang = 'ro',
  onLanguageChange,
  onAudioRegenerated
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  
  // Romanian Neural Voice selection
  const [selectedVoice, setSelectedVoice] = useState<'ro-RO-AlinaNeural' | 'ro-RO-EmilNeural'>('ro-RO-AlinaNeural');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerationNotice, setRegenerationNotice] = useState<string | null>(null);

  const fullUrl = getMediaUrl(audioUrl);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(audio.duration);
      }
    };
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [fullUrl]);

  // Restart playback if URL changes while playing
  useEffect(() => {
    if (audioRef.current && isPlaying) {
      audioRef.current.play().catch(() => {});
    }
  }, [fullUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch((e) => console.log('Audio play error:', e));
    }
  };

  const seek = (time: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const skipSeconds = (seconds: number) => {
    if (!audioRef.current) return;
    const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
    seek(newTime);
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackRate(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  };

  const handleVolumeChange = (newVol: number) => {
    setVolume(newVol);
    setIsMuted(newVol === 0);
    if (audioRef.current) {
      audioRef.current.volume = newVol;
      audioRef.current.muted = newVol === 0;
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    const targetMuted = !isMuted;
    setIsMuted(targetMuted);
    audioRef.current.muted = targetMuted;
    if (!targetMuted && volume === 0) {
      handleVolumeChange(0.8);
    }
  };

  const handleRegenerateAudio = async () => {
    if (!lessonId || isRegenerating) return;
    setIsRegenerating(true);
    setRegenerationNotice('Pregătim explicația audio…');
    try {
      const updated = await generateLessonAudio(lessonId, selectedVoice, currentLang, '+0%');
      setRegenerationNotice('Voce neurală generată cu succes!');
      setTimeout(() => setRegenerationNotice(null), 3000);
      
      const newUrl = currentLang === 'ro' 
        ? (updated.audio_url_ro || updated.audio_url) 
        : (updated.audio_url_en || updated.audio_url);
      
      if (newUrl && onAudioRegenerated) {
        onAudioRegenerated(newUrl, audioRef.current?.duration || 120);
      }
      
      if (audioRef.current) {
        audioRef.current.src = getMediaUrl(newUrl);
        audioRef.current.load();
        audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    } catch (err: any) {
      console.error(err);
      setRegenerationNotice('Eroare la generare. Vă rugăm reîncercați.');
      setTimeout(() => setRegenerationNotice(null), 4000);
    } finally {
      setIsRegenerating(false);
    }
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-white border border-[#DFE3D9] rounded-lg p-5 shadow-xs transition-shadow hover:shadow-sm">
      <audio ref={audioRef} src={fullUrl} preload="metadata" />

      {/* Header bar - LinkedIn Enterprise Style */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-[#ECEEE7]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-[#EDF2E9] text-[#315D50] flex items-center justify-center font-bold">
            <Headphones className="w-5 h-5 text-[#315D50]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-[#315D50] uppercase tracking-wide">
                {lessonNumber ? `Lecția ${lessonNumber}` : 'Narațiune Audio'}
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#E8EFE4] text-[#3E6650] border border-[#3E6650]/20">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3E6650]" />
                Explicații audio
              </span>
            </div>
            <h3 className="text-sm font-bold text-[#25382F] leading-tight line-clamp-1">
              {title}
            </h3>
          </div>
        </div>

        {/* Voice Selector & Regeneration Controls */}
        <div className="flex items-center gap-2">
          {/* Voice Picker */}
          <div className="flex items-center border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2]">
            <button
              onClick={() => setSelectedVoice('ro-RO-AlinaNeural')}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-full transition-all ${
                selectedVoice === 'ro-RO-AlinaNeural'
                  ? 'bg-white text-[#315D50] shadow-xs'
                  : 'text-[#68736B] hover:text-[#25382F]'
              }`}
            >
              Alina (Naturală)
            </button>
            <button
              onClick={() => setSelectedVoice('ro-RO-EmilNeural')}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-full transition-all ${
                selectedVoice === 'ro-RO-EmilNeural'
                  ? 'bg-white text-[#315D50] shadow-xs'
                  : 'text-[#68736B] hover:text-[#25382F]'
              }`}
            >
              Emil (Autoritar)
            </button>
          </div>

          {/* Regenerate Audio with Neural Voice */}
          {lessonId && (
            <button
              onClick={handleRegenerateAudio}
              disabled={isRegenerating}
              title="Generează sunetul din nou cu tehnologia neurală românească"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-[#315D50] hover:bg-[#EDF2E9] border border-[#315D50] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">
                {isRegenerating ? 'Se sintetizează...' : 'Regenerează Audio'}
              </span>
            </button>
          )}

          {/* Download Button */}
          {fullUrl && (
            <a
              href={fullUrl}
              download
              target="_blank"
              rel="noopener noreferrer"
              title="Descarcă fișierul audio MP3"
              className="p-1.5 rounded-full text-[#68736B] hover:text-[#25382F] hover:bg-[#F8F7F2] transition-colors"
            >
              <Download className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>

      {/* Regeneration Notice Feedback */}
      {regenerationNotice && (
        <div className="mb-3 px-3 py-1.5 bg-[#EDF2E9] border border-[#315D50]/20 rounded-md text-xs font-medium text-[#315D50] flex items-center gap-2 animate-fade-in-up">
          <Sparkles className="w-3.5 h-3.5 shrink-0" />
          <span>{regenerationNotice}</span>
        </div>
      )}

      {/* Main Scrubber / Progress Bar */}
      <div className="space-y-1.5 mb-4">
        <div 
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickPos = (e.clientX - rect.left) / rect.width;
            seek(clickPos * duration);
          }}
          className="relative w-full h-2 bg-[#DFE3D9] hover:h-2.5 rounded-full cursor-pointer transition-all overflow-hidden"
        >
          <div 
            className="absolute left-0 top-0 bottom-0 bg-[#315D50] rounded-full transition-all duration-75"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-[11px] font-medium text-[#68736B]">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Primary Playback Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Play / Skip Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => skipSeconds(-10)}
            title="Înapoi 10 secunde"
            className="p-2 rounded-full text-[#68736B] hover:text-[#25382F] hover:bg-[#F8F7F2] transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pauză' : 'Redă'}
            className="w-11 h-11 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white flex items-center justify-center shadow-xs hover:shadow-sm transition-all transform active:scale-95"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5 fill-current" />
            ) : (
              <Play className="w-5 h-5 fill-current ml-0.5" />
            )}
          </button>

          <button
            onClick={() => skipSeconds(10)}
            title="Înainte 10 secunde"
            className="p-2 rounded-full text-[#68736B] hover:text-[#25382F] hover:bg-[#F8F7F2] transition-colors"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>

        {/* Speed Controls (Pills) */}
        <div className="flex items-center gap-1 border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2]">
          {[1, 1.25, 1.5, 2].map((spd) => (
            <button
              key={spd}
              onClick={() => handleSpeedChange(spd)}
              className={`px-2 py-0.5 text-[11px] font-semibold rounded-full transition-all ${
                playbackRate === spd
                  ? 'bg-white text-[#315D50] shadow-xs'
                  : 'text-[#68736B] hover:text-[#25382F]'
              }`}
            >
              {spd}x
            </button>
          ))}
        </div>

        {/* Volume & Language Selector */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2">
            <button
              onClick={toggleMute}
              className="text-[#68736B] hover:text-[#25382F] transition-colors"
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-4 h-4" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              className="w-16 h-1 bg-[#DFE3D9] accent-[#315D50] rounded-lg cursor-pointer"
            />
          </div>

          {/* Bilingual Language Switcher */}
          {onLanguageChange && (
            <div className="flex items-center border border-[#DFE3D9] rounded-full p-0.5 bg-[#F8F7F2]">
              <button
                onClick={() => onLanguageChange('ro')}
                className={`px-2.5 py-1 text-[11px] font-semibold rounded-full transition-all ${
                  currentLang === 'ro'
                    ? 'bg-white text-[#315D50] shadow-xs'
                    : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                RO 🇷🇴
              </button>
              <button
                onClick={() => onLanguageChange('en')}
                className={`px-2.5 py-1 text-[11px] font-semibold rounded-full transition-all ${
                  currentLang === 'en'
                    ? 'bg-white text-[#315D50] shadow-xs'
                    : 'text-[#68736B] hover:text-[#25382F]'
                }`}
              >
                EN 🇬🇧
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
