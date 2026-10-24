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

document.addEventListener('click', event => {
  if (!(event.target instanceof Element)) return;
  const link = event.target.closest('[data-support-post], [data-project-outbound], [data-subscribe-open]');
  if (!link) return;
  const name = link.hasAttribute('data-support-post') ? 'support_post_click' : link.hasAttribute('data-project-outbound') ? 'project_website_click' : 'newsletter_open';
  gtag('event', name, {language:document.documentElement.lang});
});
