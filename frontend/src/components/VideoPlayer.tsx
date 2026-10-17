'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, RotateCw, Volume2, VolumeX, Maximize, CheckCircle2, Film } from 'lucide-react';
import { getMediaUrl } from '@/lib/api';

interface VideoPlayerProps {
  videoUrl?: string;
  title: string;
  scenes?: {
    scene: number;
    title: string;
    timestamp: string;
    speaker: string;
  }[];
  onEnded?: () => void;
}

export default function VideoPlayer({ videoUrl, title, scenes, onEnded }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(24);
  const [activeSceneIndex, setActiveSceneIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  const fullUrl = getMediaUrl(videoUrl);

  const defaultScenes = [
    { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Lesson Overview & Objectives' },
    { scene: 2, title: 'Core Summary', timestamp: '0:04', speaker: 'The High-Level Thesis' },
    { scene: 3, title: 'Key Concepts', timestamp: '0:08', speaker: 'Fundamental Frameworks' },
    { scene: 4, title: 'Diagram Analysis', timestamp: '0:12', speaker: 'Visual System Architecture' },
    { scene: 5, title: 'Real-World Case', timestamp: '0:16', speaker: 'Industry Application' },
    { scene: 6, title: 'Action Plan', timestamp: '0:20', speaker: 'Next Steps & Implementation' },
  ];

  const currentScenes = scenes && scenes.length > 0 ? scenes : defaultScenes;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      const scIdx = Math.min(Math.floor(video.currentTime / 4), currentScenes.length - 1);
      setActiveSceneIndex(scIdx);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration || 24);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      if (onEnded) onEnded();
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('ended', handleEnded);
    };
  }, [fullUrl, currentScenes.length, onEnded]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch((e) => console.log('Video error:', e));
    }
  };

  const jumpToScene = (sceneIndex: number) => {
    if (!videoRef.current) return;
    const targetSeconds = sceneIndex * 4;
    videoRef.current.currentTime = targetSeconds;
    setCurrentTime(targetSeconds);
    setActiveSceneIndex(sceneIndex);
  };

  const toggleFullscreen = () => {
    if (!videoRef.current) return;
    if (videoRef.current.requestFullscreen) {
      videoRef.current.requestFullscreen();
    }
  };

  const cycleSpeed = () => {
    const speeds = [1, 1.25, 1.5, 2];
    const nextIdx = (speeds.indexOf(playbackSpeed) + 1) % speeds.length;
    const nextSpeed = speeds[nextIdx];
    setPlaybackSpeed(nextSpeed);
    if (videoRef.current) videoRef.current.playbackRate = nextSpeed;
  };

  const [hasError, setHasError] = useState(false);

  return (
    <div className="bg-[#121212] rounded-[8px] overflow-hidden shadow-md border border-[#333333] text-white">
      {/* Video Canvas Container */}
      <div className="relative aspect-video bg-black flex items-center justify-center">
        {!hasError && fullUrl ? (
          <video
            ref={videoRef}
            src={fullUrl}
            className="w-full h-full object-contain"
            playsInline
            onError={() => setHasError(true)}
            onClick={togglePlay}
          />
        ) : (
          <div 
            onClick={togglePlay}
            className="w-full h-full bg-gradient-to-br from-[#0B1528] via-[#0F1E36] to-[#0A2540] p-6 text-white flex flex-col justify-between cursor-pointer relative"
          >
            <div className="flex items-center justify-between text-xs text-sky-200">
              <span className="px-2.5 py-0.5 rounded bg-[#315D50] font-bold text-[10px] uppercase tracking-wider">
                4next • HD
              </span>
              <span className="font-mono">{Math.floor(currentTime / 60)}:{Math.floor(currentTime % 60).toString().padStart(2, '0')}</span>
            </div>

            <div className="text-center my-auto px-4 max-w-lg mx-auto space-y-2">
              <div className="inline-block px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-[10px] font-bold uppercase">
                Scene {activeSceneIndex + 1}: {currentScenes[activeSceneIndex]?.title}
              </div>
              <h3 className="text-lg font-bold text-white line-clamp-1">{title}</h3>
              <p className="text-xs text-slate-300 line-clamp-2">{currentScenes[activeSceneIndex]?.speaker}</p>
            </div>

            <div className="text-center text-[11px] text-slate-400">
              {isPlaying ? 'Apasă pentru pauză' : 'Apasă pentru redare'}
            </div>
          </div>
        )}

        {/* Big play overlay if paused */}
        {!isPlaying && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 m-auto w-16 h-16 rounded-full bg-[#315D50]/90 hover:bg-[#315D50] text-white flex items-center justify-center transition-transform hover:scale-110 shadow-lg backdrop-blur-xs cursor-pointer"
          >
            <Play className="w-7 h-7 translate-x-0.5 fill-white" />
          </button>
        )}

        {/* Current scene watermark */}
        <div className="absolute top-3 left-3 px-2.5 py-1 bg-black/75 backdrop-blur-md rounded-[4px] text-xs font-semibold flex items-center gap-1.5 border border-white/10">
          <Film className="w-3.5 h-3.5 text-[#70B5F9]" />
          <span>Scene {activeSceneIndex + 1}: {currentScenes[activeSceneIndex]?.title}</span>
        </div>
      </div>

      {/* Video Controls Bar */}
      <div className="p-3.5 bg-[#1B1F23] border-t border-[#333333]">
        {/* Progress Bar */}
        <div className="flex items-center gap-3 mb-2.5">
          <span className="text-[11px] font-mono text-slate-400">
            {Math.floor(currentTime / 60)}:{Math.floor(currentTime % 60).toString().padStart(2, '0')}
          </span>
          <input
            type="range"
            min="0"
            max={duration || 24}
            value={currentTime}
            onChange={(e) => {
              if (videoRef.current) {
                const val = Number(e.target.value);
                videoRef.current.currentTime = val;
                setCurrentTime(val);
              }
            }}
            className="flex-1 h-1.5 bg-[#333333] rounded-full appearance-none cursor-pointer accent-[#315D50]"
          />
          <span className="text-[11px] font-mono text-slate-400">
            {Math.floor(duration / 60)}:{Math.floor(duration % 60).toString().padStart(2, '0')}
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <button
              onClick={togglePlay}
              className="w-8 h-8 rounded-full bg-[#315D50] hover:bg-[#23473C] text-white flex items-center justify-center transition-colors shadow-2xs cursor-pointer"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5 fill-white" />}
            </button>

            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.currentTime = Math.max(0, currentTime - 5);
                }
              }}
              className="p-1.5 text-slate-300 hover:text-white rounded-[4px] hover:bg-white/10 transition-colors"
              title="Rewind 5s"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.currentTime = Math.min(duration, currentTime + 5);
                }
              }}
              className="p-1.5 text-slate-300 hover:text-white rounded-[4px] hover:bg-white/10 transition-colors"
              title="Forward 5s"
            >
              <RotateCw className="w-4 h-4" />
            </button>

            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.muted = !isMuted;
                  setIsMuted(!isMuted);
                }
              }}
              className="p-1.5 text-slate-300 hover:text-white rounded-[4px] hover:bg-white/10 transition-colors"
            >
              {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={cycleSpeed}
              className="px-2 py-0.5 text-xs font-bold text-slate-200 bg-white/10 hover:bg-white/20 rounded-[4px] transition-colors border border-white/10"
            >
              {playbackSpeed}x
            </button>

            <button
              onClick={toggleFullscreen}
              className="p-1.5 text-slate-300 hover:text-white rounded-[4px] hover:bg-white/10 transition-colors"
              title="Fullscreen"
            >
              <Maximize className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Scene Navigation Strip */}
        <div className="mt-3 pt-2.5 border-t border-[#333333]">
          <p className="text-[10px] font-bold text-[#70B5F9] uppercase tracking-wider mb-1.5">
            Synchronized Scene Chapters
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-1.5">
            {currentScenes.map((sc, i) => (
              <button
                key={sc.scene}
                onClick={() => jumpToScene(i)}
                className={`px-2 py-1.5 rounded-[4px] text-left transition-all flex flex-col border ${
                  activeSceneIndex === i
                    ? 'bg-[#315D50] border-[#315D50] text-white font-semibold'
                    : 'bg-[#25282C] border-transparent hover:bg-[#2F3338] text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-[10px] opacity-75 font-mono">{sc.timestamp}</span>
                  {activeSceneIndex === i && <CheckCircle2 className="w-3 h-3 text-sky-200" />}
                </div>
                <span className="text-xs truncate font-medium">{sc.title}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
