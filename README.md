# TOAST : outils pour l'analyse sémiotique de Twitter

## Principes

- captation via la _Streaming API_ avec [Tweepy](http://www.tweepy.org/)
- stockage des _tweets_ sans modification dans une base [MongoDB](https://www.mongodb.com/)
- enrichissement du corpus (images & conversations) par déclenchement manuel :
  - données complémentaires relatives aux images et aux conversations stockées dans des bases [SQLite](https://www.sqlite.org/)
  - téléchargement des images sur le disque dur local et calcul du [SHA1](https://en.wikipedia.org/wiki/SHA-1) pour dédoublonnage technique
  - téléchargement des conversations (_scraping_ avec [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/))

## Captation

- ajuster la configuration :
  - [keys & tokens personnels des API Twitter](https://developer.twitter.com/en/apps) de l'application => `segreto.conf` (renommer `segreto.conf.dist`)
  - configuration générale => `toast.conf`
- lancer MongoDB
- lancer la captation : `python3 raccogliere.py` (stop : `Ctrl+C`)

## Enrichissement du corpus

### Images

- étudier la structure de la base images : constructeur de `PicturesSqliteDb.py`
- télécharger les images : `python3 pictures_process_queue.py`

### Conversations

- étudier la structure de la base conversations : constructeur de `ConversationsSqliteDb.py`
- identifier les _tweets_ « racine » : `python3 conversations_process_queue_get_root_tweets.py`
- télécharger les conversations : `python3 conversations_process_queue_scrape_root_tweets.py`
