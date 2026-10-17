# 4Next — ce mai trebuie adăugat sau schimbat

Actualizat: 18 octombrie 2026. Acesta este un inventar de lucru, nu o promisiune că toate funcțiile sunt deja disponibile.

## Starea de acum

Aplicația este publicată pe [Render](https://fournext-study.onrender.com), cu planul Free și date temporare. Utilizatorii pot crea conturi, încărca materiale private, publica materiale, organiza concepte și studia prin lecții, flashcarduri, quizuri, chat cu citate, notițe, evidențieri și progres. Există clase cu invitații, rating pentru materiale publice și export PDF. Uploadul și fluxurile principale au fost verificate în cloud pentru materiale în română și engleză.

Generarea AI depinde de disponibilitatea Gemini. Când furnizorul dă eroare, aplicația poate folosi extragerea locală, etichetată ca atare. Planul Render Free poate pierde conturile, materialele și fișierele la repornire, redeploy sau oprirea automată. Auditul tehnic detaliat, cu starea fiecărei cerințe din planul backend, este în [backend_architecture_audit.md](backend_architecture_audit.md); starea deploymentului este în [deployment_demo.md](deployment_demo.md).

**Incident nou, încă nerezolvat:** capturile pentru un PDF de programare C++ de 127 de pagini arată că o sesiune setată la 120 de minute a produs 3 lecții, 4 flashcarduri și 3 întrebări de quiz. Într-o lecție apar explicații și extrase cu text deteriorat sau afirmații care necesită verificare semantică; un quiz prezintă ca răspuns unic o afirmație discutabilă despre schimbarea tipului unei variabile C++. Capturile complete și analiza inițială sunt în [handoff-ul pentru agenți](../for_AI_Agents/incidente/generare-insuficienta-pdf-mare.md) și [dosarul de dovezi](../miscellaneous/ai-fail-2/README.md). Remedierea precedentă din `b2579fc` nu a rezolvat suficient rezultatul acestui caz. Nu considerați generarea pentru PDF-uri mari acceptată până la reproducere, corectarea fluxului și validarea pe întregul document.

## De făcut, în ordinea priorității

### Înainte de prezentarea hackathonului

- [ ] Confirmați cu organizatorii dacă baza existentă și codul reutilizat sunt eligibile și cum trebuie delimitată contribuția echipei.
- [ ] Validați problema cu un elev, student sau mentor și folosiți un material demonstrativ permis pentru utilizare.
- [ ] Alegeți scenariul scurt de demo: încărcarea sursei, lecție, întrebare cu citat, flashcard și quiz.
- [ ] Repetați demo-ul pe Render și pregătiți o înregistrare de rezervă; serviciul Free poate porni lent după inactivitate, iar datele se pot reseta.
- [ ] Finalizați pitch-ul în Canva și prezentați clar limitele prototipului, contribuțiile echipei și ce finanțare ar debloca.

### Următoarea rundă tehnică

- [ ] **Prioritate imediată — lecții insuficiente și calitate semantică pe PDF-uri mari.** Reproduceți cazul de 127 de pagini / 120 de minute, inspectați pipeline-ul curent și implementați procesare secvențială pe capitole sau segmente cu progres și reconcilierea acoperirii. Criteriile de test sunt în [handoff](../for_AI_Agents/incidente/generare-insuficienta-pdf-mare.md). Această activitate este documentată, nu implementată în acest commit.
- [x] Remediere locală a generării: explicațiile AI nu mai sunt înlocuite cu citate; extracție PDF fără glyph-uri duplicate, context pe toate paginile, citări prin ID, verificarea suportului și avertizare de timp. Generare: `gemini-3.1-flash-lite`; verificator independent `gemini-3.8-flash`, cu failover tehnic limitat către `gemini-3.6-flash`. Detalii și limite în [remediere_calitate_ai.md](remediere_calitate_ai.md).
- [x] Deployment `b2579fc` Live pe Render; smoke test public C++ EN: 22 pagini, explicații AI, chat conceptual și PDF. Test public RO: generare `ai_grounded`, limbă `ro`. Cheia nouă este configurată în Render Environment. CI pentru main și flavius a trecut.
- [ ] Evaluare pedagogică extinsă cu elevi/profesori și materiale din alte domenii/limbi; verificarea automată nu garantează corectitudinea fiecărei explicații.
- [ ] Bonus solicitat: până la trei documente în același spațiu, cu citare distinctă după document și pagină; necesită tratarea limitelor cumulate și a limbilor diferite.
- [ ] Adăugați persistență și backup pentru o versiune folosită de elevi; alegerea bazei, stocării și costului este încă deschisă. Demo-ul gratuit actual acceptă resetarea datelor.
- [ ] Adăugați istoric de conversații per utilizator, cu ștergere și păstrarea delimitării între conturi.
- [ ] Completați conturile cu verificare email și recuperare parolă înainte de utilizarea pe termen lung.
- [ ] Îmbunătățiți căutarea în biblioteca mare: index full-text, paginare și filtre suplimentare.
- [ ] Adăugați moderare și raportare pentru materialele publice și validați permisiunile de publicare cu utilizatorii.
- [ ] Extindeți recomandările către programa oficială și surse educaționale, numai după verificarea licențelor și a provenienței.
- [ ] Evaluați calitatea învățării cu un pilot; momentan nu avem măsurători care să demonstreze creșterea rezultatelor.

### Funcții de pitch și extindere

- [ ] Lecții audio/video extinse și modul cinematic interactiv. Audio-ul existent este la cerere; nu există încă un pipeline complet de video/cinematic.
- [ ] Camere de studiu și model de profesor personalizat găzduit, după estimarea costurilor și definirea protecției documentelor personale.
- [ ] Acces opțional prin cheile personale ale furnizorilor AI și rutarea controlată a cererilor prin prompturile de sistem ale aplicației.
- [ ] Monetizare pentru colecții specializate numai după validarea cererii, drepturilor asupra materialelor și regulilor pentru minori.
- [ ] Pachet arhivă pentru exporturi și evaluarea unui flux de conversie extern; exportul PDF curent funcționează local.

## Limite de păstrat vizibile

- Materialele scanate fără strat de text au nevoie de OCR, care nu este inclus în extractorul curent.
- Citările arată de unde provine un răspuns, nu garantează că documentul-sursă este corect.
- Datele demo de pe Render Free nu sunt stocare sigură pe termen lung.
- Funcțiile marcate mai sus ca viitoare nu trebuie prezentate drept funcții deja livrate.
