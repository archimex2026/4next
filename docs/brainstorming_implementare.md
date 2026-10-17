# 4Next — brainstorming și urmărirea implementării

Sursă: whiteboardul echipei și lista organizată de Flavius, transmise după sesiunea de brainstorming. Acest document păstrează toate ideile, inclusiv extensiile pentru pitch. Completează [direcția de produs](directie_produs_4next.md), fără a transforma ideile viitoare în promisiuni de funcționalitate disponibilă.

## Plan de implementare

Lucrarea este mare: modifică autentificarea, drepturile asupra materialelor, generarea și interfața. Ordinea de lucru urmează felii complete: cont → material privat → studiu din sursă → publicare → clasă. Sunt reutilizate FastAPI, SQLite și Next.js. Se adaugă dependențe numai pentru detectarea limbii și PDF unde biblioteca standard nu acoperă cerința.

| ID | Cerință | Comportament verificabil | Stare |
| --- | --- | --- | --- |
| C01 | Cont și resurse personale | Înregistrare, autentificare, ieșire; documentele private sunt accesibile numai proprietarului sau membrilor cu care sunt partajate explicit. | Implementat și verificat |
| C02 | Publish și upload public/privat | Privat implicit; proprietarul poate publica sau retrage materialul. Biblioteca publică și cea personală afișează date reale. | Implementat și verificat |
| C03 | Rating 1–5 și număr de voturi | Un vot per cont și material public; media și numărul de voturi sunt calculate din baza de date. | Implementat și verificat |
| C04 | Limba documentului | Detectare cu tratarea ambiguității; materialele și răspunsurile respectă limba sursei. | Implementat și verificat |
| C05 | Export PDF | Export lizibil, cu diacritice, pentru sursă, lecții, flashcarduri, quiz și pachetul complet. ILOVEAPI este o propunere de integrare; exportul local evită necesitatea unei chei plătite. | Implementat și verificat |
| C06 | Termeni și condiții | Pagină accesibilă; acord la creare cont și confirmarea drepturilor înainte de publicare. Textul juridic este un draft pentru prototip. | Pagină disponibilă; revizuire juridică înainte de lansare |
| S01 | Text highlighting | Selectarea unui fragment din sursă și salvarea evidențierii în cont, cu pagina și pozițiile sale. | Implementat și verificat |
| S02 | Cuvinte-cheie și aprofundare | Concepte extrase din sursă și opțiunea de a alege ce se studiază. | Implementat și verificat |
| S03 | Timp și profunzime | Utilizatorul alege timpul și nivelul de detaliu; acestea sunt salvate și folosite la structurarea materialelor. | Implementat și verificat |
| S04 | Chat contextual | Răspunde exclusiv din document; indică fragmente/pagini și recunoaște informația absentă. Modul extractiv și generarea cu un model sunt etichetate corect. | Implementat și verificat |
| S05 | Sugestii de concepte | Sugerează concepte din material și lecturi/materiale înrudite; oferă căutare în aplicație și link explicit de căutare Google. | Implementat și verificat |
| G01 | Clase de studiu | Creare de clase pe subiect, listă de membri și materiale partajate explicit. | Implementat și verificat |
| G02 | Invitații | Intrare într-o clasă prin cod; accesul nu expune materialele altor clase sau documentele nepartajate. | Implementat și verificat |
| A01 | Strat de system prompting | Apelurile către furnizori trec prin backend și instrucțiuni centrale; documentul este date, nu o sursă de instrucțiuni pentru aplicație. Cheile rămân pe server. | Implementat pentru Gemini; extensia multi-provider este viitoare |

## Extensii pentru pitch / finanțare

Acestea apar ca „În pregătire”, cu dependențele explicate. Nu există tarife, reduceri sau capacități de infrastructură inventate.

| ID | Idee păstrată | Ce este necesar înainte de disponibilitate |
| --- | --- | --- |
| F01 | Server propriu cu model de bază gratuit | Infrastructură GPU, buget operațional, alegerea/licența modelului, evaluare, limite de utilizare. |
| F02 | OpenAI / Claude / Gemini cu cheia utilizatorului | Conectori verificați, stocare sigură a cheilor și măsurarea costului. Reducerile sunt doar o ipoteză comercială, neconfirmată. |
| F03 | Camere proprii și profesor personalizat | Izolarea datelor, consimțământ, evaluare și infrastructură. Adaptarea prin instrucțiuni și surse nu trebuie confundată cu antrenarea efectivă a modelului. |
| F04 | Modul cinematic student–profesor | Generare multimedia, întrebări interactive și verificarea pedagogică; buget și resurse de procesare. |
| F05 | Bibliotecă de nișă cu paywall | Licențe pentru materiale, plăți, abonamente și politică editorială. Niciun conținut nu se taxează acum. |
| F06 | Același strat de instrucțiuni pentru toți furnizorii | Extinderea și testarea barierei existente la fiecare conector nou; un system prompt singur nu garantează securitatea. |

## Idei anterioare care rămân în direcție

- Pregătirea elevilor și studenților pentru examene este scopul produsului.
- Identificarea programei, maparea materiei și importul din API-uri/site-uri cu manuale necesită alegerea examenelor vizate, surse oficiale și verificarea drepturilor de utilizare. Aceste integrări nu se presupun implementate prin simpla afișare a unor sugestii.
- Profilul cu obiectiv de examen, timp și profunzime este baza personalizării; un sistem adaptiv complet se validează ulterior.
- Prezentarea în Canva se pregătește după stabilizarea demo-ului. Nu este încă realizată de această lucrare.
- Se declară explicit baza preexistentă Book2Sound/Book2Course în materialele de concurs, conform documentului de lucru.

## Verificări de acceptare

1. Două conturi diferite: al doilea nu poate citi, exporta sau accesa media unui document privat nepartajat; niciun URL direct nu ocolește verificarea.
2. Publicarea permite citirea, iar notițele, progresul și evidențierile rămân personale. Retragerea din public reface accesul privat.
3. Încărcare în română și engleză: lecțiile, cardurile și chatul păstrează limba, conținutul fiind legat de sursa reală.
4. O întrebare susținută de PDF are citare verificabilă. O întrebare absentă și o instrucțiune malițioasă din document nu produc informații inventate ori acțiuni externe.
5. Highlightul persistă după reîncărcare și nu apare în contul altui utilizator.
6. PDF-ul generat se deschide, conține textul selectat și diacriticele corecte.
7. Membrul intră cu cod, accesează materialul partajat și pierde accesul dacă partajarea este retrasă.
8. Interfața funcționează pe desktop și mobil, arată erori reale și nu maschează o eroare de acces cu date demo.

## Evidența livrării

Lucrările sunt pe branch-ul `flavius`. C01–C05, S01–S05, G01–G02 și A01 sunt conectate la fluxuri reale. C06 este disponibil ca draft de prototip. F01–F06 și integrarea programei oficiale sunt prezentate în `/roadmap` ca „În pregătire”; nu sunt servicii active.

- [x] Conturi, sesiuni, expirare/logout, preferințe și termeni la înregistrare.
- [x] Upload privat implicit, publicare/retragere, ratinguri reale și căutare inclusiv în cuvinte-cheie.
- [x] Detectarea limbii, confirmarea ambiguității și 6 limbi localizate: RO/EN/FR/DE/ES/IT.
- [x] Selecție de concepte, timp/profunzime salvate și materiale construite din fragmente verificabile.
- [x] Chat cu citări, refuz pentru lipsa sursei, întrebări de continuare legate de ultima întrebare, fără folosirea istoricului ca dovadă factuală.
- [x] Evidențieri, notițe, progres, carduri și rezultate personale, izolate între conturi.
- [x] Export local PDF Unicode; niciun serviciu de conversie plătit nu este necesar.
- [x] Clase, invitații, partajare și revocare; cod nou după eliminarea unui membru.
- [x] Sursă/media/export verificate la fiecare acces; protecție Origin, sesiuni HttpOnly și cote de generare.
- [x] Maximum 15 MB/fișier, 16 MiB/cerere înainte de parser, 500 pagini și limite pentru arhive/text.
- [x] Audio la cerere RO/EN: serviciul indisponibil produce eroare, fără fișiere silențioase prezentate ca rezultat.
- [x] Frontend: lint, TypeScript și build de producție.
- [x] GitHub Actions pentru backend/frontend pe `flavius`, `main` și PR-uri.
- [ ] Gemini și TTS cu servicii reale/chei valide: nu sunt validate end-to-end; testele simulează furnizorii, iar rularea locală a folosit extragerea locală.
- [ ] Deployment public complet, verificare email/recuperare parolă, proceduri juridice/retenție și infrastructură multi-worker.
- [ ] Funcțiile F01–F06 și maparea la programa oficială, după cercetare/finanțare.
- [ ] Prezentarea Canva și confirmarea eligibilității bazei preexistente conform regulamentului.

### Verificări efectuate

**Rezultat local: 52/52 teste backend trecute**, lint fără erori/avertismente, TypeScript și build de producție reușite.

Suita backend folosește baze temporare și verifică accesul între conturi, expirarea sesiunilor, ratingurile, revocarea accesului, limba, citările reale și false, prompt injection, numele de fișiere, arhivele, highlights, PDF-ul și limitele de utilizare. Acoperirea măsurată pentru codul activ este 89%; configurația exclude explicit generatoarele video/diagrame moștenite care nu sunt apelate de fluxul curent.

În browser au fost exercitate: creare cont, preferințe, introducerea textului, analiză RO, selectare concept, creare curs privat, notițe/progres, flashcarduri, quiz cu punctaj, chat RO/EN cu citări, refuzul unei întrebări absente, salvare highlight, descărcare PDF, creare clasă/partajare și rating public. Verificare vizuală desktop 1440 px și mobil 390 px, fără overflow orizontal în clase și spațiul de studiu; fără erori relevante în consola acestor fluxuri.

Selectorul de fișiere nu a putut fi automatizat deoarece pluginul Chrome a refuzat accesul la calea locală. Încărcarea multipart/PDF, extragerea și exportul sunt verificate separat prin API și teste. Primul blocaj de review automat din sesiune (limită de utilizare) a fost depășit în sesiunea următoare.

### Limite deliberate

Chatul strict oferă citate verificate și îndrumare pedagogică, nu o explicație liberă garantată factual de un model. O citare corectă nu dovedește adevărul unei parafraze arbitrare; de aceea acel text al modelului nu este afișat. La un buget scurt de studiu se selectează fragmente din sursă, fără a afirma că întreaga carte este acoperită.

Cotele upload/audio sunt comune instanțelor care folosesc aceeași bază SQLite. Concurența și limita chatului rămân per proces; sunt necesare o coadă comună și limite la proxy pentru extindere. SQLite și directoarele locale trebuie înlocuite sau găzduite persistent înainte de Vercel/publicare.

Referințe tehnice primare folosite la verificare: [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/), [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).
