let sampleVideo = document.getElementById('video');
let videoName = sampleVideo.childNodes[1].src.slice(58);
videoName = videoName.replace('.mp4', '');
console.log(videoName.length);
console.log(videoName);

// USING AN IIFE TO FETCH THE RESUMING TIME OF THE VIDEO 
(
    () => {
        getCurrentTime = localStorage.getItem(`${videoName}ResumeTime`);
        sampleVideo.currentTime = getCurrentTime - 1;
    }
)();

// WHEN THE USER SWITCHES THE WINDOW OR IT GETS DESTROYED THEN THE CURRENT PLAYBACK TIME OF THE VIDEO IS SAVED IN LOCAL STORAGE 
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        localStorage.setItem(`${videoName}ResumeTime`, sampleVideo.currentTime);
        return;
    }
    else {
        return;
    }
});