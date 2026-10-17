# Auditul planului de backend 4Next

Audit al bazei funcționale din 17 octombrie 2026, actualizat pentru migrarea Render. Integrarea fast-forward din `flavius` în `main` și push-ul sunt realizate. Planul de referință este `H:\4Next\backend_architecture_plan.md`, redactat înaintea implementării conturilor și a spațiului de studiu. Tabelul compară toate cele 30 de puncte ale planului cu implementarea reală. O alternativă funcțională nu înseamnă că tehnologia propusă există deja.

| Nr | Cerință din plan | Stare și dovadă în cod | Diferență sau pas rămas |
| --- | --- | --- | --- |
| 1 | Pydantic BaseSettings | Alternativă parțială: `backend/app/config.py` citește configurația și `.env`, folosind variabile de mediu prioritare. | Nu există model BaseSettings sau validare completă de configurație la pornire. Cheia Gemini este exclusiv pe server. |
| 2 | SQLAlchemy async | Alternativă implementată: `database.py` folosește SQLite, conexiuni cu timeout și foreign keys; accesul este verificat central. | Nu există ORM sau motor async. Arhitectura este potrivită unei singure instanțe, nu unei promisiuni enterprise. |
| 3 | Alembic | Alternativă parțială: `init_db()` creează schema și aplică modificări aditive compatibile cu datele vechi. | Nu există istoric Alembic, downgrade și management complet de versiuni. Backup înaintea migrării unei baze reale. |
| 4 | Excepții și mapping HTTP | Alternativă parțială: `HTTPException`, validarea Pydantic și mesaje explicite pentru acces, surse și furnizori. | Nu există ierarhie proprie de excepții și handler global structurat. |
| 5 | JSON logging și correlation IDs | Neimplementat în baza verificată: logare Uvicorn standard. | Necesită logare structurată fără corpuri de documente, parole sau chei. |
| 6 | Middleware și limite | Parțial: `request_limits.py`, `generation_limits.py`, Origin/CORS, cookie și cache private, cote persistente pentru generare. | Timing și request IDs nu existau în baza verificată. Chatul și concurența rămân per proces. |
| 7 | User și autentificare | Alternativă implementată: `security.py`, `routers/auth.py`, PBKDF2 SHA256 cu 600000 iterații, sesiuni aleatoare cu token hash în DB și cookie HttpOnly. | Nu folosește bcrypt/JWT/refresh tokens. Sesiunile sunt revocabile și expiră. Nu este necesară schimbarea algoritmului doar pentru a copia planul. |
| 8 | Endpoints auth și password reset | Parțial: register, login, logout, me și actualizare profil există, cu limitarea încercărilor. | Recuperarea parolei și verificarea emailului lipsesc. Conturile sunt de prototip. |
| 9 | Dependency injection | Implementat: `require_user` și `optional_user`, plus `check_book_access` și `check_course_access` pentru resurse. | Autorizarea se aplică inclusiv sursei, exportului și media. |
| 10 | Detectarea limbii | Implementat cu `langdetect`, în `services/language.py`; RO/EN/FR/DE/ES/IT. Ambiguitatea cere confirmare. | Limbile nesuportate produc eroare. Confirmarea nu permite traducerea unei limbi detectate sigur. |
| 11 | Keywords și highlighting | Implementat extractiv: `study_ai.py`, preview-ul de upload și `routers/study.py`; selecții personale validate față de sursă. | Nu este un motor semantic NLP extern. Selecția conceptelor influențează cursul. |
| 12 | Gemini în upload | Implementat opțional: `ai_analyzer.py` și `study_ai.py`, apelate din fluxul de generare. | Providerul este simulat în teste; disponibilitatea live și cheia nu se deduc din teste. Eșecul folosește extragere locală etichetată. |
| 13 | Timp profunzime focus | Implementat: minute 5–120, brief/standard/deep și focus_keywords validate și persistate. | Bugetul scurt selectează fragmente și nu acoperă întreaga carte. |
| 14 | Multi-provider audio premium | Parțial: Edge TTS cu fallback gTTS în `audio_generator.py`; RO/EN, la cererea proprietarului. | Gemini TTS și ElevenLabs nu sunt conectate. Ionuț lucrează separat la audio/video; integrarea cere review comun. |
| 15 | Normalizare audio FFmpeg | Neimplementat în generatorul activ. FFmpeg este utilizat de codul video moștenit. | Nu se poate declara o normalizare loudness sau pipeline premium validat. |
| 16 | Catalog voci premium | Parțial: voce implicită per limbă și parametru API pentru voce/ritm, cu validarea limbii. | Catalog premium și selector complet nu există. |
| 17 | Streaming audio | Alternativă parțială: `FileResponse` servește media autorizată și fișierele deja generate. | Nu există generare TTS în flux. Byte-range trebuie verificat cu fișier real și versiunea Starlette folosită la lansare. |
| 18 | RAG embeddings și vector search | Alternativă implementată: căutare lexicală pe fragmente/pagini și selecție opțională Gemini; verifică exact citatele. | Fără embeddinguri, vector DB sau căutare semantică. Textul factual liber al modelului este eliminat pentru a evita afirmații neacoperite. |
| 19 | Chat persistent | Parțial: chatul paginii și întrebări de continuare folosesc ultima întrebare doar pentru căutare. | Nu există ChatSession/ChatMessage persistate. Reîncărcarea paginii pierde conversația. |
| 20 | Source attribution | Implementat: citate exacte, număr de pagină PDF sau secțiune numerotată pentru alte formate; sursa se păstrează. | Materialele vechi fără sursă necesită reîncărcare. |
| 21 | Boundary awareness | Implementat: refuz localizat când nu există suport și apărare împotriva instrucțiunilor din document; teste pentru citări false. | O sursă poate conține erori; citarea dovedește proveniența, nu adevărul universal al textului. |
| 22 | Clase și invitații | Implementat în `routers/groups.py`: create, join code, leave, membri, share/unshare, eliminare membru. | Codul se rotește la eliminarea unui membru; materialele rămân private în afara accesului acordat explicit. |
| 23 | Publicare și retragere | Implementat: `routers/community.py`, privat implicit și publicare de către proprietar. | Drepturile asupra documentelor sunt responsabilitatea autorului publicării; text juridic de prototip. |
| 24 | Rating și voturi | Implementat: 1–5, un vot per cont/material public, medie și număr reale; fără vot pe propriul material. | Fără sistem separat de recenzii sau moderare editorială. |
| 25 | Bibliotecă și filtre | Parțial: `courses.py` și interfața publică oferă căutare, vedere public/personal, date de limbă/rating și ordine după creare. | Nu există paginare pe server și toate filtrele/sortările enterprise din plan. |
| 26 | SQLite FTS5 | Alternativă parțială: căutare casefold în titlu, autor și keywords pentru materialele accesibile. | Fără index FTS5 și fără căutare integrală în toate lecțiile. Scanarea bibliotecii nu este pentru volume mari. |
| 27 | Recomandări de lecturi | Implementat extractiv: concepte înrudite din sursă și materiale accesibile în aceeași limbă, prin suprapunerea keywords. | Nu este recomandare semantică evaluată și nu importă programa oficială. |
| 28 | Google proxy cu preview | Alternativă implementată: link explicit către Google și căutare internă. | Fără proxy, scraping sau preview extern. Deschiderea Google scoate utilizatorul din aplicație. |
| 29 | PDF complet | Implementat cu `fpdf2` și font Unicode în `pdf_export.py`; sursă, lecții, flashcards, quiz, all. | ILOVEAPI/ReportLab/WeasyPrint nu sunt necesare exportului curent. Integrarea colegului pentru conversie se tratează separat. |
| 30 | Exporturi consolidate | Parțial: PDF, Markdown, Anki TSV; audio/video/diagramă exportabile dacă există fișierul/diagrama. | Fără generare video activă în spațiul nou și fără pachet ZIP unic. Nu se creează fișiere false când lipsește furnizorul. |

## Concluzia auditului

Planul nu este implementat integral în forma sa tehnică. Funcțiile principale de studiu, conturi, colaborare și PDF sunt implementate, unele prin alternative mai simple. Nu prezentăm prototipul ca platformă enterprise și nu echivalăm existența unui fișier legacy cu integrarea sa în fluxul curent.

Ordinea sigură de lucru este: verificarea PDF pe document real și izolare între conturi, coș cu restaurare și retenție cinci zile, persistența backendului pentru demo și testarea autentificării din URL-ul public. Îmbunătățirile audio/video se coordonează cu Ionuț. Password reset, istoricul chatului, FTS5 și observabilitatea rămân diferențe explicite dacă nu sunt adăugate și testate separat. Rescrierea în ORM/JWT sau adăugarea unui vector DB nu reprezintă o condiție pentru un demo verificabil.

## Evidență și actualizare

Baza anterioară a trecut 52 de teste backend, cu 89% acoperire pentru codul activ, plus lint, TypeScript și build frontend. Aceste numere descriu verificarea anterioară, nu certifică schimbările noi. Rezultatul final al sesiunii și configurația publică se consemnează în README și checklistul de implementare după rularea verificărilor.

Coșul este implementat și verificat; publicarea URL-ului este verificată separat înainte de confirmare. Fișierul de plan este o propunere a echipei, nu o instrucțiune de a publica secrete sau de a înlocui automat componente funcționale.

Verificare nouă din această rundă: **78/78 teste backend, 90% acoperire pentru codul activ, 5/5 teste proxy frontend**, lint, TypeScript și build de producție reușite. Gateway-ul izolat respinge accesul direct fără secret, iar răspunsul Next real nu expune antetele interne. Generarea reală Gemini a produs un material `ai_grounded`. Detalii de deployment în [deployment_demo.md](deployment_demo.md).

## Decizia de găzduire după incidentul 502

Demo-ul Vercel anterior depindea de backendul de pe PC. Echipa a raportat eroare 502 după sleep, astfel că ținta de găzduire s-a schimbat: un Web Service Docker pe Render, cu Next.js pe portul public `PORT` și FastAPI numai la `127.0.0.1:8000`. Proxyul păstrează API-ul și cookie-urile pe aceeași origine. Nu mai folosim un tunel către calculator pentru ținta oficială.

Echipa a ales explicit Free, fără disc și fără activarea facturării. Datele SQLite, uploadurile și media sunt temporare sub `/var/data`; restartul, redeployul și oprirea automată pot reseta conturile și fișierele. Serviciul Free se oprește după 15 minute fără trafic, iar accesul următor poate avea aproximativ un minut de pornire. Autentificarea în Render, preview-ul Blueprint, crearea serviciului și deploymentul Live sunt realizate. [Documentația Render Free](https://render.com/docs/free)

Persistența este o opțiune ulterioară, prin disc pe serviciu cu plată sau prin baze și stocare externe, după aprobarea bugetului. Nu este inclusă în demo-ul Free ales.

Cele 78 de teste backend, 90% acoperire și cinci teste proxy descriu verificarea locală a sursei pregătite pentru Render. Buildul Docker și smoke testul containerului pentru frontend, API, SQLite, catalog și PDF au trecut în CI 39066911100. Deploymentul Live a fost verificat pe https://fournext-study.onrender.com. Testele cloud au acoperit conturi, upload PDF în română și engleză, generare cu fallback etichetat, citări/refuzuri, exporturi, clase, publicare și izolare între utilizatori. Gemini poate returna erori ServerError; fallbackul extractiv a trecut testele. Datele Free rămân temporare și pot fi resetate. Instrucțiunile operaționale sunt în [deployment_demo.md](deployment_demo.md).
