# 4Next

4Next este un spațiu de studiu pentru elevi și studenți: adaugi materialele tale, alegi conceptele, timpul și profunzimea, apoi studiezi prin lecții, flashcarduri, quizuri și întrebări ancorate în sursă. Pregătirea pentru examene este direcția produsului.

Versiunea curentă este un prototip funcțional, publicat pe Render la [fournext-study.onrender.com](https://fournext-study.onrender.com). Interfața și API-ul rulează împreună, independent de calculatorul echipei. Fluxurile cloud testate includ autentificarea, uploadul PDF, generarea extractivă/AI, citările, exporturile PDF, studiul și clasele. Demo-ul folosește planul Free: datele pot fi resetate, iar furnizorul Gemini poate fi indisponibil; în acel caz este folosit fallbackul extractiv etichetat. Demo-ul Vercel anterior este retras din rolul de adresă oficială. Sursa verificată este integrată și publicată pe **main** și **flavius**; funcțiile pentru finanțare sunt prezentate separat în pagina „Ce urmează”.

## Funcții disponibile

| Zonă | Ce funcționează |
| --- | --- |
| Cont | Înregistrare, login/logout, sesiuni cu cookie HttpOnly, preferințe de timp/profunzime și obiectiv de examen. |
| Materiale | PDF, EPUB, DOCX, TXT, MD sau text lipit; analiză înainte de generare, concepte selectabile, sursă păstrată. |
| Coș | Ștergere reversibilă pentru cinci zile, restaurare ca material privat și ștergere definitivă. Expirarea se verifică la pornire și la solicitările API. |
| Limbă | Detectare automată pentru română, engleză, franceză, germană, spaniolă și italiană. Cazurile nesigure cer confirmarea limbii originale. |
| Studiu | Lecții cu fragmente citate, flashcarduri și quizuri din sursă; progresul și notițele sunt personale. |
| Chat | Caută în document, indică pagini/fragmente și refuză întrebările pentru care nu găsește suport. Conversația curentă rămâne în memoria paginii. |
| Evidențieri | Selecții salvate în cont, cu pagină și poziții verificate față de textul sursă. |
| Publicare | Materialele sunt private implicit; proprietarul le poate publica/retrage. Biblioteca publică are căutare, rating 1–5 și număr real de voturi. |
| Clase | Creare, coduri de invitație, membri și partajare explicită. Retragerea materialului sau eliminarea unui membru revocă accesul; codul se schimbă la eliminare. |
| Sugestii | Concepte din document, materiale accesibile înrudite și legături explicite către căutări în aplicație sau Google. |
| Export | PDF cu diacritice: sursă, lecții, carduri, quiz sau pachet complet. API-ul păstrează și exporturile Markdown/Anki. |
| Audio | Generare opțională la cererea proprietarului pentru surse în RO/EN, în limba documentului. Depinde de servicii TTS externe; eșecurile sunt afișate. |
| Informare | Pagini de termeni și confidențialitate pentru prototip, plus roadmap cu funcțiile viitoare marcate clar. |

## Cum folosește AI-ul sursa

Gemini este opțional și este apelat doar din backend, prin instrucțiuni pedagogice centrale. Documentele și întrebările sunt tratate ca date neîncrezute; modelul nu are instrumente sau dreptul de a executa acțiuni.

**Explicațiile, cardurile și quizurile generate sunt păstrate** după validarea structurii, limbii și citărilor și un apel separat care verifică suportul în sursă. Serverul rezolvă identificatorii de citare la fragmentele originale; modelul nu inventează pagini. Această verificare reduce erorile, fără să garanteze adevărul fiecărei explicații. Fără furnizor disponibil sau la respingerea verificării, interfața afișează explicit că sunt disponibile doar extrase. Generarea folosește implicit `gemini-3.1-flash-lite` (`GEMINI_MODEL`), iar verificarea factuală un model separat, `gemini-3.8-flash` (`GEMINI_VERIFIER_MODEL`). Ideile-cheie nesusținute pot fi omise; o explicație nesusținută este respinsă.

Documentele lungi trimit către AI un context limitat la 75.000 de caractere, distribuit între toate paginile. Sesiunile scurte oferă o selecție sau un overview, cu avertisment înainte și după generare; nu promit parcurgerea întregii cărți. Extragerea PDF elimină caracterele suprapuse și watermarkurile diagonale mari, păstrând numerele reale ale paginilor. Pentru TXT/MD/DOCX/EPUB, reperele sunt secțiuni numerotate; pentru PDF sunt paginile extrase.

## Limite și funcții viitoare

Upload: maximum **15 MB în backend** (limita interfeței și a proxyului se configurează pentru deployment), **500 de pagini PDF**, **1.000.000 de caractere**; arhivele sunt limitate și după decomprimare. PDF-urile scanate necesită OCR înainte de încărcare. Fișierele DOC vechi trebuie convertite în DOCX. Limbile nesuportate sunt respinse explicit, fără traducere automată.

Limite pe cont: 5 generări de materiale/minut și 30/zi; audio 3/minut și 20/zi; inspecție 10/minut; chat 15/minut. Maximum trei generări simultane pe proces și una pentru același cont. Cotele pentru upload/audio sunt păstrate în SQLite; concurența și limita chatului sunt locale procesului.

**În pregătire:** identificarea programei oficiale, server AI propriu cu acces gratuit de bază, chei personale OpenAI/Claude/Gemini, camere cu tutor personalizat/antrenare, mod cinematic interactiv și bibliotecă de nișă cu acces plătit. Acestea necesită cercetare, infrastructură, licențe sau finanțare. Nu există abonamente, reduceri ori plăți active.

Conturile locale nu au încă verificare email, recuperare parolă sau ștergere completă de cont din interfață. Materialele vechi fără sursă păstrată trebuie reîncărcate pentru chat/export de sursă; uploadurile vechi fără proprietar nu sunt publicate automat.

## Pornire locală

Necesită **Python 3.11+** și **Node.js 20.9+**. Din rădăcina proiectului, într-un terminal PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

În alt terminal, din rădăcina proiectului:

```powershell
cd frontend
npm ci
npm run dev
```

Aplicația: [localhost:3000](http://localhost:3000). API și documentație: [localhost:8000/docs](http://localhost:8000/docs). La prima pornire sunt adăugate două exemple educaționale originale, RO/EN, fără apeluri către modele sau generare media.

Configurația opțională se găsește în [backend/.env.example](backend/.env.example) și [frontend/.env.example](frontend/.env.example). Cheia Gemini rămâne pe server. PDF-ul folosește Arial pe Windows sau DejaVu Sans pe Linux; se poate seta `PDF_FONT_PATH`.

## Verificări

Din rădăcina proiectului:

```powershell
backend\.venv\Scripts\python.exe -m coverage run --source=backend/app -m unittest discover -s backend/tests -v
backend\.venv\Scripts\python.exe -m coverage report
cd frontend
npm run lint
npx tsc --noEmit
node --test tests/proxy.test.mjs
npm run build
```

Ultima verificare locală a sursei pregătite pentru Render: **89/89 teste backend**, **90% acoperire pentru codul activ**, **5/5 teste proxy frontend**, lint fără erori/avertismente, TypeScript și build reușite.

Sunt testate autentificarea și expirarea sesiunilor, izolarea între conturi, publicarea/ratingurile, revocarea accesului în clase, limba/citările, atacurile prin documente, uploadurile, PDF-ul Unicode și limitele de utilizare. Testele folosesc baze temporare și modele simulate, fără servicii plătite. Acoperirea configurată exclude generatoarele video/diagrame moștenite care nu sunt conectate la fluxul curent. GitHub Actions rulează verificările pentru push pe `flavius`/`main` și pentru PR-uri.

## Stocare și lansare

Ținta curentă este **un singur Web Service Docker pe Render**. Next.js primește traficul public pe portul `PORT`; proxyul intern trimite `/api` și `/media` către FastAPI, disponibil numai în container la `127.0.0.1:8000`. Browserul păstrează aceeași origine pentru interfață și cookie, fără tunel către PC și fără un backend public separat.

Echipa a ales explicit **Render Free pentru demo, cu date temporare**. SQLite, uploadurile și media se scriu sub `/var/data`, fără disc persistent: conturile și fișierele se pot pierde la restart, redeploy sau oprirea automată. După 15 minute fără trafic, serviciul Free se oprește, iar următorul acces îl reactivează în aproximativ un minut. Contul demo se creează în interfață și poate necesita recreare după reset. Nu este activat niciun plan cu plată. [Render Free](https://render.com/docs/free)

Pentru păstrarea datelor ulterior, aceeași arhitectură poate folosi un serviciu cu disc persistent, după aprobarea costului și testarea backupului. [Render Persistent Disks](https://render.com/docs/disks)

Configurația este în [render.yaml](render.yaml), [Dockerfile.render](Dockerfile.render) și [scripts/run_render.py](scripts/run_render.py). Blueprintul Free Frankfurt folosește `main`, fără disc și cu publicare manuală. Schema oficială și preview-ul Blueprint din Render au fost validate. [GitHub Actions 39066911100](https://github.com/archimex2026/4next/actions/runs/39066911100) a trecut toate cele trei joburi, inclusiv buildul și testarea reală a containerului. Serviciul Render Free este Live, iar verificările cloud pentru homepage, health, catalog, PDF și fluxurile de studiu au trecut, cu fallback extractiv disponibil când Gemini eșuează. Cheia Gemini este configurată în mediul Render cu aprobarea utilizatorului; cheia rămâne secret de server. Valorile locale `.env`, SQLite, parolele și fișierele utilizatorilor nu intră în Git sau în imaginea Docker. Textele juridice rămân drafturi pentru prototip.

Planul, pașii din Dashboard, configurația de mediu și verificările înainte de lansare sunt în [deployment_demo.md](docs/deployment_demo.md). Prototipul Vercel cu API pe PC a trecut anterior verificări publice, apoi echipa a raportat 502 după intrarea PC-ului în sleep. Acele verificări sunt istoric, nu dovadă de disponibilitate curentă. Adresa Vercel nu mai este ținta de lansare.

## Documente de lucru

- [Checklist și brainstorming complet](docs/brainstorming_implementare.md)
- [Direcția produsului](docs/directie_produs_4next.md)
- [Sistemul vizual](DESIGN.md)
- [Auditul celor 30 de puncte din planul backend](docs/backend_architecture_audit.md)
- [Structura templateului de pitch](docs/prezentare_template.md)
- [Documentul de lucru actualizat](docs/4Next_document_de_lucru_hackathon.docx)

Proiectul evoluează din baza preexistentă Book2Sound/Book2Course. Această proveniență trebuie declarată în materialele de concurs. Prezentarea Canva și livrabilele finale de hackathon se pregătesc după stabilizarea demo-ului.
