# 4Next

4Next este un spațiu de studiu pentru elevi și studenți: adaugi materialele tale, alegi conceptele, timpul și profunzimea, apoi studiezi prin lecții, flashcarduri, quizuri și întrebări ancorate în sursă. Pregătirea pentru examene este direcția produsului.

Versiunea curentă este un prototip funcțional local. Lucrăm pe branch-ul **flavius**; funcțiile pentru finanțare sunt prezentate separat în pagina „Ce urmează”.

## Funcții disponibile

| Zonă | Ce funcționează |
| --- | --- |
| Cont | Înregistrare, login/logout, sesiuni cu cookie HttpOnly, preferințe de timp/profunzime și obiectiv de examen. |
| Materiale | PDF, EPUB, DOCX, TXT, MD sau text lipit; analiză înainte de generare, concepte selectabile, sursă păstrată. |
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

Versiunea strictă afișează **fragmente exacte verificate și îndrumări pedagogice localizate**. Când este disponibil, modelul selectează fragmentele relevante; textul factual liber produs de model nu este afișat doar pentru că are atașată o citare. Fără cheie validă sau când serviciul nu răspunde, aplicația funcționează prin extragere locală, etichetată în interfață.

Documentele de peste 100.000 de caractere folosesc extragerea locală pentru construirea cursului. Un interval scurt de studiu selectează fragmente, fără să pretindă că acoperă o carte întreagă. Pentru TXT/MD/DOCX/EPUB, reperele sunt secțiuni numerotate; pentru PDF sunt paginile extrase.

## Limite și funcții viitoare

Upload: maximum **15 MB**, **500 de pagini PDF**, **1.000.000 de caractere**; arhivele sunt limitate și după decomprimare. PDF-urile scanate necesită OCR înainte de încărcare. Fișierele DOC vechi trebuie convertite în DOCX. Limbile nesuportate sunt respinse explicit, fără traducere automată.

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
npm run build
```

Ultima verificare locală: **52/52 teste backend**, **89% acoperire pentru codul activ**, lint fără erori/avertismente, TypeScript și build reușite.

Sunt testate autentificarea și expirarea sesiunilor, izolarea între conturi, publicarea/ratingurile, revocarea accesului în clase, limba/citările, atacurile prin documente, uploadurile, PDF-ul Unicode și limitele de utilizare. Testele folosesc baze temporare și modele simulate, fără servicii plătite. Acoperirea configurată exclude generatoarele video/diagrame moștenite care nu sunt conectate la fluxul curent. GitHub Actions rulează verificările pentru push pe `flavius`/`main` și pentru PR-uri.

## Stocare și lansare

SQLite, uploadurile și media sunt locale și excluse din Git. Docker Compose definește stocare persistentă pentru baza de date și directoarele media/upload; configurația nu a fost validată într-un deployment public.

Vercel rămâne destinația propusă pentru interfață. Publicarea completă necesită backend și stocare persistente, HTTPS, `COOKIE_SECURE=true`, origini CORS explicite și o configurație frontend/API compatibilă cu cookie-urile SameSite. Sistemul curent este potrivit pentru o singură instanță; extinderea cere cozi și limite comune tuturor workerilor. Textele juridice sunt drafturi pentru prototip.

## Documente de lucru

- [Checklist și brainstorming complet](docs/brainstorming_implementare.md)
- [Direcția produsului](docs/directie_produs_4next.md)
- [Sistemul vizual](DESIGN.md)

Proiectul evoluează din baza preexistentă Book2Sound/Book2Course. Această proveniență trebuie declarată în materialele de concurs. Prezentarea Canva și livrabilele finale de hackathon se pregătesc după stabilizarea demo-ului.
