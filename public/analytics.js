'use strict';
window.dataLayer = window.dataLayer || [];
function gtag(){window.dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-1DPNCQB9NC');

document.addEventListener('click', event => {
  const button = event.target instanceof Element
    ? event.target.closest('#copy-prompt, [data-copy-prompt]') : null;
  if (!button) return;
  gtag('event', 'dot_prompt_copy_click', {
    language: document.documentElement.lang,
    prompt_location: button.hasAttribute('data-copy-prompt') ? 'community' : 'participate'
  });
});
