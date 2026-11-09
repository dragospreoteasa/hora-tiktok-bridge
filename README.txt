HORA ROMANILOR - ANDROID + NETLIFY + RENDER (prototip)

Ce este in ZIP:
- index.html: versiune a jocului cu muzica si camp pentru adresa serverului
- server.py: asculta evenimente TikTok LIVE si le publica prin /events
- requirements.txt, render.yaml: pentru gazduire Render

ATENTIE: Prototipul nu este conectat inca si nu a fost testat cu un LIVE real. Biblioteca TikTokLive este neoficiala.

1. Pe telefon creeaza un repository privat GitHub numit hora-tiktok-bridge si incarca server.py, requirements.txt si render.yaml.
2. Intra pe dashboard.render.com, conecteaza GitHub, creeaza Web Service si selecteaza repository-ul. Start: uvicorn server:app --host 0.0.0.0 --port $PORT ; Build: pip install -r requirements.txt
3. Username-ul TIKTOK_USERNAME este deja configurat: dragospreoteasa. ALLOWED_ORIGIN este deja configurat: https://dovik-f3697e.netlify.app
4. Cand Render porneste, testeaza adresa de forma https://hora-tiktok-bridge.onrender.com/ si verifica 'configured':true.
5. Pe Netlify publici separat index.html din acest pachet in loc de pagina veche (pastrez muzica locala prin Alege MP3).
6. In joc, introduci URL Render (fara /events), apesi Conecteaza si astepti conectarea.
7. Intri LIVE in TikTok cu Mobile Gaming si pornesti partajarea ecranului. La comentariul HORA ar trebui sa intre spectatorul. La cadouri se declanseaza animatii.

Limitari:
- Render gratuit intra in repaus si nu e adecvat pentru LIVE-uri fiabile/lungi; foloseste plan always-on daca e nevoie.
- TikTokLive e API neoficial si se poate bloca sau schimba fara anunt. Unele servere pot fi respinse.
- Pe un singur telefon, aplicația TikTok poate suspenda Chrome in fundal; testeaza daca jocul si sunetul raman active.
- Daca numele in TikTok nu corespunde, nu primesti evenimente; nu trimite parole sau session cookies.
- Foloseste doar muzica pe care ai dreptul sa o difuzezi LIVE.
