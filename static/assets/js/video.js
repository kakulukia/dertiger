let sampleVideo = document.getElementById('video');

// USING AN IIFE TO FETCH THE RESUMING TIME OF THE VIDEO 
(
    () => {
        getCurrentTime = localStorage.getItem('resumeTime');
        sampleVideo.currentTime = getCurrentTime - 1;
    }
)();

// WHEN THE USER SWITCHES THE WINDOW OR IT GETS DESTROYED THEN THE CURRENT PLAYBACK TIME OF THE VIDEO IS SAVED IN LOCAL STORAGE 
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        localStorage.setItem('resumeTime', sampleVideo.currentTime);
        return;
    }
    else {
        return;
    }
});