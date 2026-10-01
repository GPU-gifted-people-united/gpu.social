'use strict';
const english = document.documentElement.lang === 'en';
const copy = {
  'Связаться с разработчиками': 'Contact the developers',
  'Внедрён': 'Deployed',
  'Расскажи, что нужно твоему бизнесу. Команда мастерской рассмотрит запрос и поможет связаться с разработчиками.': 'Tell us what your business needs. The workshop team will review your request and help you connect with the developers.',
  'Какая задача у вашего бизнеса и что хотите обсудить с разработчиками?': 'What does your business need, and what would you like to discuss with the developers?',
  'В разработке': 'In development', 'В архиве': 'Archived', 
  'Хочу попробовать': 'Try it', 'Посмотреть': 'Explore', 'Мне это нужно': 'I need this',
  'В каталоге пока нет проектов.': 'There are no projects in the catalogue yet.',
  'Пока собираем идеи и задачи. Расскажи, какая вещь тебе нужна, или предложи свой проект.': 'We are gathering ideas. Tell us what you need, or share a project of your own.',
  'Предложить задачу ↗': 'Suggest an idea ↗',
  'Ничего не нашли. Попробуй другой запрос или предложи свою задачу.': 'Nothing found. Try another search or suggest an idea.',
  'Не удалось загрузить каталог. ': 'Could not load the catalogue. ', 'Попробовать ещё раз': 'Try again',
  'Попробовать ': 'Try ', 'Вернуть ': 'Bring back ', 'Добавить свой проект': 'Add your project',
  'Какой вещи не хватает?': 'What do you wish existed?',
  'Проект ещё в разработке. Расскажи, что ты хотел бы попробовать. Сохраним твой интерес к тестированию.': 'This project is still in development. Tell us what you would like to try, and we will save your interest in testing.',
  'Расскажи, для чего тебе нужен этот проект. Мы сохраним запрос, но не обещаем сроков возвращения.': 'Tell us how you would use this project. We will save your request, but cannot promise a release date.',
  'Работающий, незаконченный или уже остановленный — расскажи, чем он может быть полезен.': 'Working, unfinished, or already stopped: tell us why it could be useful.',
  'Опиши реальную ситуацию. Сначала посмотрим, нет ли уже подходящего решения.': 'Describe a real situation. We will first see whether something suitable already exists.',
  'Что делает проект, кому нужен и работает ли сейчас?': 'What does it do, who needs it, and does it work now?',
  'Что нужно сделать и в какой ситуации это пригодится?': 'What should it do, and when would someone need it?',
  'Сохраняем…': 'Saving…', 'Отправить заявку ↗': 'Send submission ↗',
  'Не удалось сохранить заявку. Попробуй ещё раз.': 'Could not save your submission. Please try again.',
  'Твой запрос на этот проект уже есть в списке. Повторно отправлять его не нужно.': 'We already have your request for this project. No need to send it again.',
  'Заявка сохранена. Команда мастерской посмотрит её и сможет связаться с тобой.': 'Your submission is saved. The workshop team will review it and may contact you.',
  'Нет связи с сервером. Текст заявки остаётся в форме.': 'Cannot reach the server. Your text is still in the form.',
  'Отправьте заявку через форму на сайте.': 'Please use the form on this site.',
  'Заявка слишком большая.': 'Your submission is too large.',
  'Неверный формат.': 'Invalid submission format.',
  'Не удалось отправить форму.': 'Could not send the form.',
  'Проект не найден.': 'Project not found.',
  'Проверьте обязательные поля и длину описания.': 'Check the required fields and description length.',
  'Укажите email, Telegram @username или ссылку на профиль LinkedIn.': 'Enter an email, Telegram @username, or LinkedIn profile URL.',
  'Ссылка должна начинаться с https:// или http://.': 'The link must start with https:// or http://.',
  'Нужно согласие на обработку заявки.': 'Please agree to have your submission stored.',
  'Слишком много заявок. Попробуйте через час.': 'Too many submissions. Please try again in an hour.'
};
const tr = value => english ? (copy[value] || value) : value;
const $ = selector => document.querySelector(selector);
const cards = $('#cards'), modal = $('#submit-dialog'), form = $('#submission');
let projects = [], filter = 'all';
function el(tag, cls, value) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (value !== undefined) node.textContent = value;
  return node;
}
function render() {
  cards.replaceChildren();
  const b2bCards = $('#b2b-cards'); b2bCards.replaceChildren();
  const q = $('#search').value.trim().toLocaleLowerCase(english ? 'en' : 'ru');
  const rows = projects.filter(p => (filter === 'all' || (filter === 'b2b' ? p.category === 'B2B' : p.status === filter)) &&
    [p.title, p.description, p.category, p.author].join(' ').toLocaleLowerCase(english ? 'en' : 'ru').includes(q));
  $('#count').textContent = projects.length;
  $('.filters').hidden = !projects.length;
  document.querySelector('[data-filter="b2b"]').hidden = !projects.some(p => p.category === 'B2B');
  $('.search').hidden = !projects.length;
  $('#b2b').hidden = !rows.some(p => p.category === 'B2B');
  for (const p of rows) {
    const card = el('article', 'card');
    const kind = p.id === 'pinock-space' ? 'space' : p.id === 'logo-maker' ? 'logo' : p.id === 'yukaresearch' ? 'research' : 'generic';
    const art = el('div', 'card-art ' + kind);
    art.setAttribute('aria-hidden', 'true');
    art.append(el('strong', '', kind === 'space' ? 'space /' : kind === 'logo' ? 'Aa → Logo' : kind === 'research' ? 'Research.' : p.title));
    const body = el('div', 'card-body'), meta = el('div', 'card-meta');
    meta.append(el('span', '', p.category));
    const status = p.category === 'B2B' && p.status === 'live' ? 'Внедрён' : p.status === 'development' ? 'В разработке' : p.status === 'archived' ? 'В архиве' : '';
    if (status) meta.append(el('span', 'status ' + (p.status === 'archived' ? 'archived' : ''), tr(status)));
    body.append(meta, el('h3', '', p.title), el('p', '', p.description));
    const bottom = el('div', 'card-bottom'); bottom.append(el('span', 'author', p.author));
    if (p.category === 'B2B') {
      const button = el('button', 'card-action', tr('Связаться с разработчиками'));
      button.type = 'button'; button.append(el('span', '', '↗')); button.onclick = () => openForm('contact', p); bottom.append(button);
    } else if (p.status === 'live' && /^https?:\/\//.test(p.url)) {
      const link = el('a', 'card-action', tr(p.id === 'actor-replacement-studio' ? 'Хочу попробовать' : 'Посмотреть'));
      link.href = p.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.append(el('span', '', '↗')); bottom.append(link);
    } else {
      const button = el('button', 'card-action', tr(p.status === 'development' ? 'Хочу попробовать' : 'Мне это нужно'));
      button.type = 'button'; button.append(el('span', '', '↗')); button.onclick = () => openForm('revive', p); bottom.append(button);
    }
    body.append(bottom); card.append(art, body); (p.category === 'B2B' ? b2bCards : cards).append(card);
  }
  if (!projects.length) {
    const empty = el('div', 'empty');
    empty.append(el('h3', '', tr('В каталоге пока нет проектов.')), el('p', '', tr('Пока собираем идеи и задачи. Расскажи, какая вещь тебе нужна, или предложи свой проект.')));
    const button = el('button', 'button', tr('Предложить задачу ↗')); button.onclick = () => openForm('idea'); empty.append(button); cards.append(empty);
  } else if (!rows.length) cards.append(el('p', 'empty', tr('Ничего не нашли. Попробуй другой запрос или предложи свою задачу.')));
}
async function load() {
  try {
    const response = await fetch(english ? '/en/api/projects' : '/workshop/api/projects');
    if (!response.ok) throw Error();
    projects = await response.json(); render();
    if (location.hash === '#b2b' && !$('#b2b').hidden) $('#b2b').scrollIntoView();
  } catch {
    const message = el('p', 'empty', tr('Не удалось загрузить каталог. '));
    const retry = el('button', 'retry', tr('Попробовать ещё раз')); retry.onclick = load; message.append(retry); cards.replaceChildren(message);
  }
}
for (const button of document.querySelectorAll('[data-filter]')) button.onclick = () => {
  filter = button.dataset.filter;
  for (const item of document.querySelectorAll('[data-filter]')) {
    item.classList.toggle('selected', item === button); item.setAttribute('aria-pressed', String(item === button));
  }
  render();
};
$('#search').addEventListener('input', render);
function openForm(kind, project) {
  form.reset(); form.hidden = false; $('#success').hidden = true; $('#form-error').textContent = '';
  form.elements.kind.value = kind; form.elements.project_id.value = project?.id || '';
  const isProject = kind === 'project', revive = kind === 'revive', contact = kind === 'contact', linked = revive || contact;
  $('#dialog-title').textContent = contact ? tr('Связаться с разработчиками') + ' — ' + project.title : revive ? tr(project.status === 'development' ? 'Попробовать ' : 'Вернуть ') + project.title : tr(isProject ? 'Добавить свой проект' : 'Какой вещи не хватает?');
  $('#dialog-intro').textContent = tr(contact ? 'Расскажи, что нужно твоему бизнесу. Команда мастерской рассмотрит запрос и поможет связаться с разработчиками.' : revive ? (project.status === 'development' ? 'Проект ещё в разработке. Расскажи, что ты хотел бы попробовать. Сохраним твой интерес к тестированию.' : 'Расскажи, для чего тебе нужен этот проект. Мы сохраним запрос, но не обещаем сроков возвращения.') : isProject ? 'Работающий, незаконченный или уже остановленный — расскажи, чем он может быть полезен.' : 'Опиши реальную ситуацию. Сначала посмотрим, нет ли уже подходящего решения.');
  $('#title-field').hidden = linked; form.elements.title.required = !linked;
  $('#author-field').hidden = !isProject; form.elements.author.required = isProject;
  $('#url-field').hidden = !isProject;
  form.elements.description.placeholder = tr(contact ? 'Какая задача у вашего бизнеса и что хотите обсудить с разработчиками?' : isProject ? 'Что делает проект, кому нужен и работает ли сейчас?' : 'Что нужно сделать и в какой ситуации это пригодится?');
  modal.showModal();
}
for (const button of document.querySelectorAll('[data-kind]')) button.onclick = () => openForm(button.dataset.kind);
for (const button of document.querySelectorAll('[data-close]')) button.onclick = () => button.closest('dialog').close();
$('#privacy-open').onclick = () => $('#privacy-dialog').showModal();
for (const dialog of document.querySelectorAll('dialog')) dialog.addEventListener('click', event => {
  if (event.target === dialog) {
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  }
});
form.addEventListener('submit', async event => {
  event.preventDefault(); const button = form.querySelector('[type=submit]');
  button.disabled = true; button.textContent = tr('Сохраняем…'); $('#form-error').textContent = '';
  const data = Object.fromEntries(new FormData(form)); data.consent = form.elements.consent.checked;
  try {
    const response = await fetch('/workshop/api/submissions', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    const result = await response.json();
    if (!response.ok) throw Error(tr(result.error || 'Не удалось сохранить заявку. Попробуй ещё раз.'));
    form.hidden = true; $('#success').hidden = false;
    $('#success-text').textContent = tr(result.duplicate ? 'Твой запрос на этот проект уже есть в списке. Повторно отправлять его не нужно.' : 'Заявка сохранена. Команда мастерской посмотрит её и сможет связаться с тобой.');
  } catch (error) {
    $('#form-error').textContent = error.message || tr('Нет связи с сервером. Текст заявки остаётся в форме.');
  } finally {button.disabled = false; button.textContent = tr('Отправить заявку ↗');}
});
load();
