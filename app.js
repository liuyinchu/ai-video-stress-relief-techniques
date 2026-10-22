const film = document.querySelector('#film');
const start = document.querySelector('#play-film');
const chapters = [...document.querySelectorAll('.chapter')];
const error = document.querySelector('#playback-error');
let pendingTime = null;

function playPending() {
  if (pendingTime === null || film.readyState < 1) return;
  film.currentTime = Math.min(pendingTime, film.duration);
  pendingTime = null;
  film.play().catch(() => { film.focus(); });
}

function watch(time) {
  error.hidden = true;
  pendingTime = time;
  document.querySelector('#watch').scrollIntoView({
    behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    block: 'start'
  });
  playPending();
  if (film.networkState === HTMLMediaElement.NETWORK_EMPTY) film.load();
}

start.addEventListener('click', () => watch(0));
chapters.forEach(button => button.addEventListener('click', () => watch(Number(button.dataset.start))));
film.addEventListener('loadedmetadata', playPending);
film.addEventListener('play', () => { start.firstChild.textContent = '从头观看 '; });
film.addEventListener('error', () => { error.hidden = false; });
film.addEventListener('timeupdate', () => {
  let current = null;
  for (const chapter of chapters) if (film.currentTime >= Number(chapter.dataset.start)) current = chapter;
  for (const chapter of chapters) {
    if (chapter === current) chapter.setAttribute('aria-current', 'true');
    else chapter.removeAttribute('aria-current');
  }
});
