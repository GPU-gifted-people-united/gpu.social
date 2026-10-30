"""Public HTML, news and discovery. Only published catalogue fields are read."""
import json,re
from datetime import datetime,timezone
from html import escape as esc
from urllib.parse import urlparse
from xml.etree.ElementTree import Element,SubElement,tostring

SITE='https://gpu.social'
VISIBLE="('live','development','archived')"

def categories(app):
 return json.loads((app.ROOT/'public/categories.json').read_text())

def category_for(app,p):
 groups=categories(app)
 known=next((g for g in groups if p['id'] in g['projects']),None)
 if known:return known
 value=p['category'].casefold()
 direct=next((g for g in groups if value in [g['id'],*(v.casefold() for v in g['label'].values())]),None)
 if direct:return direct
 legacy={'b2b':'business','финансы':'everyday','finance':'everyday','еда':'everyday','food':'everyday','события':'everyday','events':'everyday','видео и голос':'content','video and voice':'content','видео':'content','video':'content','текстовый контент':'content','written content':'content','графический контент':'content','graphic content':'content'}
 return next(g for g in groups if g['id']==legacy.get(value,'tools'))

def decorate_category(app,p,en=False):
 group=category_for(app,p)
 p['category_id']=group['id'];p['category_label']=group['label']['en' if en else 'ru']

def category_url(group,en=False):
 return ('/en/categories/' if en else '/workshop/categories/')+group['id']+'/'

def category_nav(app,rows,en=False,selected='all'):
 language='en' if en else 'ru'
 home=('/en/' if en else '/')+'#projects'
 links=f'<a class="filter {"selected" if selected=="all" else ""}" href="{home}" data-category="all" aria-current="{"true" if selected=="all" else "false"}">{"All" if en else "Все"} <span>{len(rows)}</span></a>'
 for group in categories(app):
  count=sum(p['category_id']==group['id'] for p in rows)
  if not count:continue
  active=selected==group['id']
  links+=f'<a class="filter {"selected" if active else ""}" href="{category_url(group,en)}" data-category="{group["id"]}" aria-current="{"true" if active else "false"}">{esc(group["label"][language])} <span>{count}</span></a>'
 return '<nav class="filters category-filters" aria-label="'+('Project categories' if en else 'Категории проектов')+'">'+links+'</nav>'

def category_page(app,group,en=False):
 language='en' if en else 'ru';rows=projects(app,en)
 chosen=[p for p in rows if p['category_id']==group['id']]
 title=group['title'][language];description=group['description'][language]
 search='<label class="search"><input type="search" id="search" aria-label="'+('Search projects' if en else 'Поиск проектов')+'" placeholder="'+('Search projects' if en else 'Найти проект')+'"></label>'
 main=f'<main id="main" class="news-page category-page" data-category="{group["id"]}"><a class="text-button" href="{"/en/" if en else "/"}#projects">← {"All projects" if en else "Все проекты"}</a><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p><section class="catalog"><div class="section-head">{search}</div>{category_nav(app,rows,en,group["id"])}<p class="catalog-count" id="catalog-count" role="status"></p><div id="cards" class="cards">{"".join(card(p,en) for p in chosen)}</div></section>{subscription_invite(en)}</main>'
 schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':description,'url':SITE+category_url(group,en),'mainEntity':{'@type':'ItemList','numberOfItems':len(chosen),'itemListElement':[{'@type':'ListItem','position':i+1,'name':p['title'],'url':SITE+project_url(p,en)} for i,p in enumerate(chosen)]}}
 return page(app,main,title+' — GPU',description,category_url(group),category_url(group,True),en,schema)

def projects(app,en=False):
 with app.connect() as d:rows=[dict(r) for r in d.execute(f'SELECT * FROM projects WHERE status IN {VISIBLE} ORDER BY created,id')]
 if en:
  for p in rows:app.localize_english_project(p)
 for p in rows:decorate_category(app,p,en)
 return rows

def stories(app):
 visible={p['id'] for p in projects(app)}
 return [s for s in json.loads((app.ROOT/'public/stories.json').read_text()) if s['project_id'] in visible]

def story_url(story,en=False):
 return ('/en/stories/' if en else '/workshop/stories/')+story['id']+'/'

def story_references(item,available):
 ids={urlparse(u).path.rstrip('/').split('/')[-1] for u in item.get('project_urls',[])}
 return [{'url':SITE+story_url(story),'url_en':SITE+story_url(story,True),'title':story['title']['ru'],'title_en':story['title']['en']} for story in available if story['project_id'] in ids]

def story_post(story,en=False):
 language='en' if en else 'ru'
 return story['post'][language]+'\n'+SITE+story_url(story,en)+'\n\n'+('Built something too? Bring it to GPU — we’ll spread the word together.' if en else 'Тоже что-то сделал? Приноси в GPU — будем продвигать вместе.')

def story_links(app,item,en=False):
 ids={urlparse(u).path.rstrip('/').split('/')[-1] for u in item.get('project_urls',[])}
 return ''.join(f'<a class="text-button" href="{story_url(s,en)}">{esc(s["title"]["en" if en else "ru"])} →</a>' for s in stories(app) if s['project_id'] in ids)

def story_page(app,story,en=False):
 language='en' if en else 'ru'
 p=next(p for p in projects(app,en) if p['id']==story['project_id'])
 title=story['title'][language];description=story['summary'][language]
 sections=''
 for section in story['sections']:
  sections+='<section><h2>'+esc(section['heading'][language])+'</h2>'
  sections+=''.join('<p>'+esc(text)+'</p>' for text in section.get('paragraphs',{}).get(language,[]))
  steps=section.get('steps',{}).get(language,[])
  if steps:sections+='<ol>'+''.join('<li>'+esc(text)+'</li>' for text in steps)+'</ol>'
  sections+='</section>'
 demo=''
 if story.get('demo_image'):
  demo=f'<figure><img src="{esc(story["demo_image"],quote=True)}" alt="{esc(story["image_alt"][language],quote=True)}" width="1366" height="900" loading="lazy"><figcaption>{esc(story["image_alt"][language])}</figcaption></figure><button type="button" class="button" data-play-game>{"Play here" if en else "Играть здесь"} ▷</button>'
 main=f'<main id="main" class="news-page story-page"><a class="text-button" href="{"/en/stories/" if en else "/workshop/stories/"}">← {"Project stories" if en else "Истории проектов"}</a><time datetime="{esc(story["date_published"])}">{story["date_published"][:10]}</time><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p><p class="muted">{"GPU editorial team · Maker: " if en else "Редакция GPU · Создали проект: "}{esc(p["author"])}</p><article class="story-body">{sections}{demo}<p class="story-source">{esc(story["source_note"][language])} <a href="{esc(story["source_url"],quote=True)}" target="_blank" rel="noopener noreferrer">{"Source" if en else "Источник"} ↗</a></p></article><div class="actions"><a class="button" href="{project_url(p,en)}">{"Try the project" if en else "Попробовать проект"} →</a><button class="text-button" id="share-news">{"Copy post" if en else "Скопировать пост"}</button><span id="share-news-status" role="status"></span></div><details class="agent-details"><summary>{"Ready-to-share post" if en else "Готовый текст для публикации"}</summary><div class="agent-details-body"><textarea id="news-post-text" readonly rows="9" aria-label="{"Post text" if en else "Текст поста"}">{esc(story_post(story,en))}</textarea></div></details>{subscription_invite(en)}</main>'
 schema={'@context':'https://schema.org','@type':'Article','headline':title,'description':description,'datePublished':story['date_published'],'inLanguage':language,'mainEntityOfPage':SITE+story_url(story,en),'author':{'@type':'Organization','name':'GPU editorial team'},'publisher':{'@type':'Organization','name':'Gifted People United','url':SITE+'/'},'about':{'@type':'SoftwareApplication','name':p['title'],'url':SITE+project_url(p,en)},'citation':story['source_url']}
 if story.get('demo_image'):schema['image']=SITE+story['demo_image']
 return page(app,main,title+' — GPU',description,story_url(story),story_url(story,True),en,schema)

def news(app):
 items=json.loads((app.ROOT/'updates.json').read_text())
 with app.connect() as d:
  runtime=[json.loads(r[0]) for r in d.execute('SELECT data FROM runtime_updates')]
  posts=[dict(r) for r in d.execute('SELECT * FROM update_posts ORDER BY created,url')]
 visible_ids={p['id'] for p in projects(app)}
 runtime=[i for i in runtime if i.get('kind')!='project-update' or i.get('source_project_id') in visible_ids]
 known={i['id'] for i in items}
 items=items+[i for i in runtime if i['id'] not in known]
 available_stories=stories(app)
 for item in items:
  item['stories']=story_references(item,available_stories)
  item['story_urls']=[story['url'] for story in item['stories']]
  for post in posts:
   if post['update_id']==item['id']:
    existing=item.setdefault('social_posts',[])
    if not any(p['url']==post['url'] for p in existing):existing.append({'platform':post['platform'],'url':post['url']})
    item['date_modified']=datetime.fromtimestamp(post['created'],timezone.utc).isoformat().replace('+00:00','Z')
 return sorted(items,key=lambda i:datetime.fromisoformat(i['date_published'].replace('Z','+00:00')).timestamp(),reverse=True)

def post_text(app,item,en=False):
 title=item.get('title_en',item['title']) if en else item['title']
 summary=item.get('summary_en',item['summary']) if en else item['summary']
 ids={urlparse(u).path.rstrip('/').split('/')[-1] for u in item.get('project_urls',[])}
 rows=[p for p in projects(app,en) if p['id'] in ids]
 story_text=''.join('\n'+u.replace('/workshop/stories/','/en/stories/') if en else '\n'+u for u in item.get('story_urls',[]))
 return title+'\n\n'+summary+('\n'+item['external_url'] if item.get('external_url') else '')+story_text+'\n\n'+'\n\n'.join(p['title']+' — '+p['author']+'\n'+p['description']+'\n'+SITE+project_url(p,en) for p in rows)+'\n\n'+('Try a project, share feedback, and bring your own — we’ll spread the word together.' if en else 'Пробуйте, делитесь отзывами и приносите своё — будем продвигать вместе.')+'\n'+SITE+news_url(item,en)

def feed(app):
 items=[]
 for source in news(app):
  item=dict(source);item['url']=SITE+news_url(item);item['url_en']=SITE+news_url(item,True)
  item['content_text']=item['summary']+('\n'+item['external_url'] if item.get('external_url') else '')+''.join('\n'+u for u in item.get('story_urls',[]))+''.join('\n'+p['platform']+': '+p['url'] for p in item.get('social_posts',[]))
  items.append(item)
 return {'version':'https://jsonfeed.org/version/1.1','title':'GPU / Updates','home_page_url':SITE+'/','feed_url':SITE+'/workshop/feed.json','items':items}

def news_url(item,en=False):
 return ('/en/news/' if en else '/workshop/news/')+item['id']+'/'

def project_url(p,en=False):
 return ('/en/projects/' if en else '/workshop/projects/')+p['id']+'/'

def social_links(item,en=False):
 result=[]
 for post in item.get('social_posts',[]):
  url=post.get('url','');host=urlparse(url).hostname
  if urlparse(url).scheme!='https' or host not in ('www.linkedin.com','linkedin.com','t.me'):continue
  name=post.get('platform','LinkedIn')
  label=('Support on ' if en else 'Поддержать в ')+name
  result.append(f'<a class="text-button" data-support-post href="{esc(url,quote=True)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>')
 return ''.join(result)

def card(p,en=False):
 href=project_url(p,en);kind='business' if p['category']=='B2B' else 'tools'
 action=''
 if p['status']=='live' and urlparse(p['url']).scheme in ('http','https'):
  action=f'<a class="card-action" data-project-outbound href="{esc(p["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{"Visit website" if en else "Перейти на сайт"} ↗</a>'
 elif p['category']=='B2B':action=f'<a class="card-action" href="{href}">{"Contact the developers" if en else "Связаться с разработчиками"} ↗</a>'
 if p['id']=='baattle-royale' and p['status']=='live':action=f'<button type="button" class="card-action" data-play-game>{"Play here" if en else "Играть здесь"} ▷</button>'+action
 label=esc(p.get('category_label',p['category']))
 if p.get('category_id'):label=f'<a href="{category_url({"id":p["category_id"]},en)}">{label}</a>'
 return f'<article class="card k-{kind}"><div class="card-meta"><span class="card-tags"><span class="chip">{label}</span></span><span class="author">{esc(p["author"])}</span></div><h3><a href="{href}">{esc(p["title"])}</a></h3><p class="card-desc">{esc(p["description"])}</p><div class="card-bottom">{action}</div></article>'

def news_card(item,en=False,app=None):
 title=item.get('title_en',item['title']) if en else item['title']
 summary=item.get('summary_en',item['summary']) if en else item['summary']
 return f'<article class="update"><time datetime="{esc(item["date_published"])}">{esc(item["date_published"][:10])}</time><div><h3><a href="{news_url(item,en)}">{esc(title)}</a></h3><p>{esc(summary)}</p></div><div class="actions"><a class="text-button" href="{news_url(item,en)}">{"View projects" if en else "Посмотреть проекты"} ↗</a>{social_links(item,en)}{story_links(app,item,en) if app else ""}</div></article>'

def subscription_invite(en=False):
 return f'<div class="subscribe-invite"><p>{"New projects. Only when there is news." if en else "Новые проекты. Только когда есть новости."}</p><a class="button" data-subscribe-open href="{"/en/subscribe/" if en else "/workshop/subscribe/"}">{"Get updates" if en else "Получать новинки"}</a></div>'

def page(app,main,title,description,ru,en_path,en=False,schema=None):
 html=(app.ROOT/'public'/('index-en.html' if en else 'index.html')).read_text()
 html=re.sub(r'<main id="main">.*?</main>',lambda _:main,html,count=1,flags=re.S)
 html=re.sub(r'<title>.*?</title>',lambda _:f'<title>{esc(title)}</title>',html,count=1)
 for key,value in [('name="description"',description),('property="og:title"',title),('property="og:description"',description)]:
  html=re.sub('<meta '+key+r' content="[^"]*">',lambda _,k=key,v=value:f'<meta {k} content="{esc(v,quote=True)}">',html,count=1)
 ru_current='aria-current="page"' if not en else '';en_current='aria-current="page"' if en else ''
 html=re.sub(r'<span class="lang-switch">.*?</span></header>',lambda _:f'<span class="lang-switch"><a href="{ru}" lang="ru" {ru_current}>RU</a><span>/</span><a href="{en_path}" lang="en" {en_current}>EN</a></span></header>',html,count=1)
 extra=f'<link rel="canonical" href="{SITE+(en_path if en else ru)}"><link rel="alternate" hreflang="ru" href="{SITE+ru}"><link rel="alternate" hreflang="en" href="{SITE+en_path}"><link rel="alternate" hreflang="x-default" href="{SITE+en_path}"><meta property="og:url" content="{SITE+(en_path if en else ru)}">'
 if schema:
  data=json.dumps(schema,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
  extra+='<script type="application/ld+json">'+data+'</script>'
 return html.replace('</head>',extra+'</head>')

def homepage(app,en):
 html=(app.ROOT/'public'/('index-en.html' if en else 'index.html')).read_text()
 rows=projects(app,en);regular=''.join(card(p,en) for p in rows)
 html=re.sub(r'<div id="cards".*?</div>',lambda _:f'<div id="cards" class="cards" aria-live="polite">{regular}</div>',html,count=1,flags=re.S)
 html=re.sub(r'<div class="filters".*?</div>',lambda _:category_nav(app,rows,en)+'<p class="catalog-count" id="catalog-count" role="status"></p>',html,count=1,flags=re.S)
 html=re.sub(r'<div id="updates">.*?</div>',lambda _:'<div id="updates">'+''.join(news_card(i,en,app) for i in news(app)[:4])+'</div>',html,count=1,flags=re.S)
 match=re.search(r'<main id="main">.*?</main>',html,re.S)
 main=match[0]
 main=main.replace('<div id="updates">',subscription_invite(en)+'<div id="updates">',1)
 main=main.replace('</main>',f'<p class="news-archive"><a class="text-button" href="{"/en/news/" if en else "/workshop/news/"}">{"All updates" if en else "Все новости"} →</a></p></main>')
 schema={'@context':'https://schema.org','@type':'CollectionPage','name':'GPU Social','publisher':{'@type':'Organization','@id':SITE+'/#community','name':'Gifted People United','url':SITE+'/','sameAs':['https://github.com/GPU-gifted-people-united/gpu.social','https://t.me/GiftedPeopleUnited']},'url':SITE+('/en/' if en else '/'),'mainEntity':{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':SITE+project_url(p,en),'name':p['title']} for i,p in enumerate(rows)]}}
 return page(app,main,'GPU — '+('projects by Gifted People United' if en else 'проекты сообщества Gifted People United'),'Community-built projects to explore, try and share.' if en else 'Проекты сообщества: пробуйте полезные инструменты, знакомьтесь с авторами и добавляйте своё.','/','/en/',en,schema)

def project_page(app,p,en):
 if en:app.localize_english_project(p)
 decorate_category(app,p,en)
 group=category_for(app,p)
 title=esc(p['title']);author=esc(p['author']);category=esc(p.get('category_label',p['category']));description=esc(p['description'])
 action=''
 if p['status']=='live' and app.valid_url(p['url']):action=f'<a class="button" data-project-outbound href="{esc(p["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{"Visit website" if en else "Перейти на сайт"} ↗</a>'
 if p['category']=='B2B' or not action:action+=f'<button class="button ghost" id="project-contact">{("Contact the developers" if en else "Связаться с разработчиками") if p["category"]=="B2B" else ("I want to try it" if en else "Хочу попробовать")} ↗</button>'
 demo=''
 if p['id']=='baattle-royale' and p['status']=='live':
  action=f'<button class="button" id="play-here">{"Play here" if en else "Играть здесь"} ▷</button>'+action
  demo=f'<dialog id="game-dialog" class="game-dialog" aria-labelledby="game-title"><div class="dialog-top"><h2 id="game-title">Baattle Royale</h2><button class="close" type="button" data-close aria-label="{"Close game" if en else "Закрыть игру"}">×</button></div><p class="muted">{"A game by Maks Kurilenko. If it does not load, open the developer’s website." if en else "Игра Maks Kurilenko. Если не загрузится — открой сайт автора."} <a href="https://baattleroyale.com/" target="_blank" rel="noopener noreferrer">{"Open website" if en else "Открыть сайт"} ↗</a></p><div id="game-container"></div></dialog>'
 fields=json.loads((app.ROOT/'public/project-details.json').read_text()).get(p['id'],{})
 language='en' if en else 'ru';details=''
 labels={'audience':('Кому пригодится','Who it is for'),'example':('Пример использования','Example use'),'platforms':('Платформы','Platforms'),'access':('Условия доступа','Access')}
 for key,(ru_label,en_label) in labels.items():
  value=fields.get(key,{}).get(language)
  if value:details+=f'<div><h2>{en_label if en else ru_label}</h2><p>{esc(value)}</p></div>'
 related=[i for i in news(app) if any(urlparse(u).path.rstrip('/')==project_url(p).rstrip('/') for u in i.get('project_urls',[]))]
 related_html=''
 guides=[story for story in stories(app) if story['project_id']==p['id']]
 if guides:related_html='<section class="project-updates"><h2>'+('Project story & guide' if en else 'История и знакомство с проектом')+'</h2>'+''.join(f'<p><a class="text-button" href="{story_url(story,en)}">{esc(story["title"]["en" if en else "ru"])} →</a></p>' for story in guides)+'</section>'
 if related:related_html+='<section class="project-updates"><h2>'+('Updates & community posts' if en else 'Новости и публикации')+'</h2>'+''.join(news_card(i,en,app) for i in related)+'</section>'
 similar=[other for other in projects(app,en) if other['category_id']==group['id'] and other['id']!=p['id']][:3]
 if similar:related_html+='<section class="project-updates"><h2>'+('More in this category' if en else 'Ещё в этой категории')+'</h2><div class="cards">'+''.join(card(other,en) for other in similar)+'</div></section>'
 updated=f'<p class="muted">{"Description updated" if en else "Описание обновлено"}: {esc(fields["updated"])}</p>' if fields.get('updated') else ''
 main=f'<main id="main" class="project-page" data-project-id="{esc(p["id"])}" data-project-title="{title}" data-project-status="{esc(p["status"])}" data-project-category="{esc(p["category"])}"><a class="text-button" href="{"/en/" if en else "/"}#projects">← {"All projects" if en else "Все проекты"}</a><p class="eyebrow"><a href="{category_url(group,en)}">{category}</a></p><h1>{title}</h1><p class="lead">{description}</p><p class="author">{"Made by" if en else "Создали"}: {author}</p><div class="actions">{action}<a class="text-button" href="{"/en/updates/new/" if en else "/workshop/updates/new/"}?project={esc(p["id"],quote=True)}">{"Suggest an update" if en else "Предложить обновление"}</a><button class="text-button" id="share-project">{"Share this project" if en else "Поделиться проектом"} ↗</button><span id="share-status" role="status"></span></div><section class="project-facts">{details}</section>{updated}{related_html}{subscription_invite(en)}{demo}</main>'
 schema={'@context':'https://schema.org','@type':'SoftwareApplication','name':p['title'],'description':p['description'],'url':SITE+project_url(p,en),'applicationCategory':p['category_label'],'author':{'@type':'Person','name':p['author']},'inLanguage':language}
 if fields.get('platforms',{}).get('en'):schema['operatingSystem']=fields['platforms']['en']
 if p['url']:schema['sameAs']=p['url']
 return page(app,main,p['title']+' — GPU',p['description'],project_url(p),project_url(p,True),en,schema)

def news_page(app,item,en):
 title=item.get('title_en',item['title']) if en else item['title'];summary=item.get('summary_en',item['summary']) if en else item['summary']
 ids={urlparse(u).path.rstrip('/').split('/')[-1] for u in item.get('project_urls',[])}
 rows=[p for p in projects(app,en) if p['id'] in ids]
 body=''.join(card(p,en) for p in rows)
 external=''
 if item.get('external_url') and app.valid_url(item['external_url']):external=f'<a class="button" data-project-outbound href="{esc(item["external_url"],quote=True)}" target="_blank" rel="noopener noreferrer">{"Open update link" if en else "Открыть ссылку на обновление"} ↗</a>'
 main=f'<main id="main" class="news-page"><a class="text-button" href="{"/en/news/" if en else "/workshop/news/"}">← {"All updates" if en else "Все новости"}</a><time datetime="{esc(item["date_published"])}">{item["date_published"][:10]}</time><h1>{esc(title)}</h1><p class="lead">{esc(summary)}</p><div class="actions">{external}{social_links(item,en)}{story_links(app,item,en)}<button class="text-button" id="share-news">{"Copy post" if en else "Скопировать пост"}</button><span id="share-news-status" role="status"></span></div><details class="agent-details"><summary>{"Ready-to-share post" if en else "Готовый текст для публикации"}</summary><div class="agent-details-body"><textarea id="news-post-text" readonly rows="10" aria-label="{"Post text" if en else "Текст поста"}">{esc(post_text(app,item,en))}</textarea></div></details><div class="cards news-projects">{body}</div>{subscription_invite(en)}</main>'
 schema={'@context':'https://schema.org','@type':'BlogPosting','headline':title,'description':summary,'datePublished':item['date_published'],'inLanguage':'en' if en else 'ru','mainEntityOfPage':SITE+news_url(item,en),'publisher':{'@type':'Organization','name':'GPU — Gifted People United','url':SITE},'author':{'@type':'Organization','name':'GPU — Gifted People United'},'about':[{'@type':'SoftwareApplication','name':p['title'],'url':SITE+project_url(p,en)} for p in rows]}
 return page(app,main,title+' — GPU',summary,news_url(item),news_url(item,True),en,schema)

def update_form_page(app,en=False):
 rows=projects(app,en);options=''.join(f'<option value="{esc(p["id"],quote=True)}">{esc(p["title"])}</option>' for p in rows)
 title='Suggest a project update' if en else 'Предложить обновление проекта'
 description='Share a release, a new feature or a request for testers. GPU reviews updates before publishing them on the website, RSS feed and email newsletter.' if en else 'Расскажи о релизе, новой функции или поиске тестировщиков. После проверки новость появится на сайте, в RSS и email-подборке.'
 form=f"""<form id="update-form" class="update-form"><label>{'Project' if en else 'Проект'}<select name="project_id" required><option value="">{'Choose your project' if en else 'Выбери свой проект'}</option>{options}</select></label><label>{'Headline' if en else 'Заголовок'}<input name="title" minlength="3" maxlength="120" required placeholder="{'What is new?' if en else 'Что нового?'}"></label><label>{'Update' if en else 'Текст обновления'}<textarea name="description" rows="6" minlength="10" maxlength="3000" required placeholder="{'What changed, who is it for, and how can people try it?' if en else 'Что изменилось, кому пригодится и как попробовать?'}"></textarea></label><label>{'Link (optional)' if en else 'Ссылка (необязательно)'}<input name="url" type="url" maxlength="1000" placeholder="https://"></label><label>{'Contact for review' if en else 'Контакт для проверки'}<input name="contact" maxlength="180" required placeholder="@username, email, LinkedIn"><small>{'Only the GPU team can see it. Use the contact associated with your project when possible.' if en else 'Виден только команде GPU. По возможности укажи контакт, связанный с твоим проектом.'}</small></label><div class="trap" aria-hidden="true"><input name="website" tabindex="-1" autocomplete="off"></div><label class="consent"><input name="consent" type="checkbox" required><span>{'I agree to have this update and my contact stored for review. The update may be published after review; my contact stays private.' if en else 'Согласен на хранение обновления и контакта для проверки. Новость может быть опубликована после проверки; контакт останется приватным.'}</span></label><button class="button" type="submit">{'Send for review' if en else 'Отправить на проверку'}</button><p id="update-status" role="status"></p></form>"""
 main=f'<main id="main" class="news-page"><a class="text-button" href="{"/en/news/" if en else "/workshop/news/"}">← {"All updates" if en else "Все новости"}</a><h1>{title}</h1><p class="lead">{description}</p>{form}</main>'
 html=page(app,main,title+' — GPU',description,'/workshop/updates/new/','/en/updates/new/',en)
 return html.replace('</head>','<meta name="robots" content="noindex,follow"></head>')

def response(app,path):
 if path in ('/workshop/updates/new/','/en/updates/new/'):return 200,update_form_page(app,path.startswith('/en/')),'text/html; charset=utf-8'
 if path=='/workshop/feed.json':return 200,feed(app),'application/feed+json; charset=utf-8'
 if path=='/workshop/feed.xml':
  from email.utils import format_datetime
  root=Element('rss',version='2.0');channel=SubElement(root,'channel')
  for name,value in [('title','GPU / Updates'),('link',SITE+'/'),('description','New projects from Gifted People United')]:SubElement(channel,name).text=value
  for item in feed(app)['items']:
   row=SubElement(channel,'item')
   for name,value in [('title',item['title']),('link',item['url']),('description',item['content_text']),('guid',item['id']),('pubDate',format_datetime(datetime.fromisoformat(item['date_published'].replace('Z','+00:00'))))]:SubElement(row,name).text=value
  return 200,tostring(root,encoding='utf-8',xml_declaration=True),'application/rss+xml; charset=utf-8'
 if path in ('/','/en/'):return 200,homepage(app,path.startswith('/en/')),'text/html; charset=utf-8'
 if path in ('/workshop','/workshop/'):
  return None # Handler redirects these aliases.
 if path=='/robots.txt':return 200,'User-agent: *\nAllow: /\nDisallow: /workshop/api/\nDisallow: /en/api/\nDisallow: /workshop/subscription/\nSitemap: '+SITE+'/sitemap.xml\n','text/plain; charset=utf-8'
 match=re.fullmatch(r'/(workshop|en)/categories/([a-z-]+)/?',path)
 if match:
  group=next((g for g in categories(app) if g['id']==match[2]),None)
  if not group or not any(p['category_id']==group['id'] for p in projects(app)):return 404,{'error':'Category not found'},'application/json; charset=utf-8'
  return 200,category_page(app,group,match[1]=='en'),'text/html; charset=utf-8'
 match=re.fullmatch(r'/(workshop|en)/stories(?:/([a-z0-9-]+))?/?',path)
 if match:
  en=match[1]=='en';language='en' if en else 'ru'
  if match[2]:
   story=next((s for s in stories(app) if s['id']==match[2]),None)
   if not story:return 404,{'error':'Story not found'},'application/json; charset=utf-8'
   return 200,story_page(app,story,en),'text/html; charset=utf-8'
  title='Project stories' if en else 'Истории проектов'
  description='Practical guides, demos and stories from the GPU community.' if en else 'Знакомимся с проектами GPU: задачи, сценарии использования и демо.'
  listing=''.join(f'<article class="update"><h2><a href="{story_url(s,en)}">{esc(s["title"][language])}</a></h2><p>{esc(s["summary"][language])}</p></article>' for s in stories(app))
  invitation='Made a project? Tell us what problem it solves, show a demo and share what you learned.' if en else 'Сделал проект? Расскажи, какую задачу он решает, покажи демо и поделись тем, что получилось.'
  main=f'<main id="main" class="news-page"><h1>{title}</h1><p class="lead">{description}</p><div class="story-list">{listing}</div><p>{invitation}</p><div class="actions"><button class="button" type="button" data-kind="story">{"Tell your story" if en else "Рассказать историю"}</button><a class="text-button" href="https://t.me/GiftedPeopleUnited" target="_blank" rel="noopener noreferrer">{"Talk to GPU on Telegram" if en else "Обсудить в Telegram GPU"} ↗</a></div></main>'
  return 200,page(app,main,title+' — GPU',description,'/workshop/stories/','/en/stories/',en),'text/html; charset=utf-8'
 if path=='/sitemap.xml':
  root=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
  pairs=[('/','/en/'),('/workshop/people/','/en/people/'),('/workshop/news/','/en/news/')]+[(project_url(p),project_url(p,True)) for p in projects(app)]+[(news_url(i),news_url(i,True)) for i in news(app)]
  pairs += [('/workshop/stories/','/en/stories/')]+[(story_url(s),story_url(s,True)) for s in stories(app)]
  present={p['category_id'] for p in projects(app)}
  pairs += [(category_url(g),category_url(g,True)) for g in categories(app) if g['id'] in present]
  for pair in pairs:
   for loc in pair:
    node=SubElement(root,'url');SubElement(node,'loc').text=SITE+loc
    for lang,href in zip(('ru','en'),pair):SubElement(node,'{http://www.w3.org/1999/xhtml}link',rel='alternate',hreflang=lang,href=SITE+href)
  return 200,tostring(root,encoding='utf-8',xml_declaration=True),'application/xml; charset=utf-8'
 match=re.fullmatch(r'/(workshop|en)/projects/([^/]+)/?',path)
 if match:
  with app.connect() as d:row=d.execute(f'SELECT * FROM projects WHERE id=? AND status IN {VISIBLE}',(match[2],)).fetchone()
  if not row:return 404,{'error':'Project not found'},'application/json; charset=utf-8'
  return 200,project_page(app,dict(row),match[1]=='en'),'text/html; charset=utf-8'
 match=re.fullmatch(r'/(workshop|en)/news(?:/([^/]+))?/?',path)
 if match:
  en=match[1]=='en'
  if match[2]:
   item=next((i for i in news(app) if i['id']==match[2]),None)
   if not item:return 404,{'error':'Update not found'},'application/json; charset=utf-8'
   return 200,news_page(app,item,en),'text/html; charset=utf-8'
  main='<main id="main" class="news-page"><h1>'+('What’s new at GPU' if en else 'Что нового в GPU')+'</h1><p><a class="button ghost" href="'+('/en/updates/new/' if en else '/workshop/updates/new/')+'">'+('Suggest an update' if en else 'Предложить обновление')+'</a></p><p><a class="text-button" href="'+('/en/stories/' if en else '/workshop/stories/')+'">'+('Project stories →' if en else 'Истории проектов →')+'</a></p>'+subscription_invite(en)+''.join(news_card(i,en,app) for i in news(app))+'</main>'
  return 200,page(app,main,'GPU — '+('Updates' if en else 'Новости'),'New projects and updates from Gifted People United.' if en else 'Новые проекты и новости сообщества Gifted People United.','/workshop/news/','/en/news/',en),'text/html; charset=utf-8'
 if path in ('/workshop/people/','/en/people/'):
  en=path.startswith('/en/');html=(app.ROOT/'public'/('people-en.html' if en else 'people.html')).read_text();main=re.search(r'<main id="main".*?</main>',html,re.S)[0]
  return 200,page(app,main,'PEOPLE — GPU','People building GPU together.','/workshop/people/','/en/people/',en),'text/html; charset=utf-8'
 return None
