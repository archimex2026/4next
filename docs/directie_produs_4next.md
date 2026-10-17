# Direcția produsului 4Next

4Next îi ajută pe elevi și studenți să studieze din materialele proprii și să se pregătească pentru examene. Conturile, cursurile, exersarea și citările constituie baza curentă. [Checklistul de implementare](brainstorming_implementare.md) păstrează fiecare idee; [auditul de backend](backend_architecture_audit.md) separă funcțiile existente de tehnologiile și extinderile încă neimplementate.

## Profesorul de studiu și limba sursei

Materialele derivate păstrează limba documentului: română, engleză, franceză, germană, spaniolă sau italiană. Detectarea nesigură cere confirmarea limbii originale; o detecție sigură nu poate fi schimbată pentru a traduce implicit materialul. Limbile nesuportate sunt respinse explicit. O eventuală traducere rămâne o alegere viitoare separată.

Asistentul folosește un ton răbdător și îndrumări pedagogice, fără să pretindă că este un profesor uman. În versiunea strictă, aplicația afișează fragmente exacte din sursă și instrucțiuni de învățare localizate. Gemini poate selecta fragmentele, dar proza factuală liberă a modelului nu se afișează doar pentru că are o citare atașată. Această limită previne introducerea unor explicații care nu pot fi susținute de document. Fără serviciu disponibil, extragerea locală folosește același document real și este etichetată.

## Chatul despre document

Chatul funcționează în spațiul materialului și răspunde pe baza paginilor sau secțiunilor păstrate. O întrebare susținută primește un citat verificabil; o întrebare absentă primește un refuz în limba documentului. Întrebările de continuare folosesc ultima întrebare pentru căutare, fără a transforma istoricul în dovadă factuală. Conversația nu este încă salvată după reîncărcarea paginii. Materialele vechi fără sursă trebuie reîncărcate.

Căutarea actuală este lexicală, cu selecție opțională Gemini. Nu promitem embeddinguri, vector search sau un profesor capabil să explice liber orice idee, independent de surse.

## Conturi resurse și colaborare

Contul păstrează documentele, notițele, evidențierile și progresul individual. Preferințele includ timpul, profunzimea și obiectivul de examen; la upload pot fi alese conceptele de aprofundat. Un chestionar adaptiv mai amplu rămâne o etapă ulterioară.

Documentele sunt private implicit. Proprietarul poate publica sau retrage un material și îl poate partaja explicit în clase cu cod de invitație. Ratingurile publice au voturi reale. Accesul la sursă, export și media este verificat central, iar notițele rămân personale și când materialul este public.

Coșul de gunoi permite mutarea de către proprietar, restaurarea și ștergerea definitivă, cu expirare după cinci zile. Cât timp materialul este în coș, accesul public și cel acordat clasei este oprit. Implementarea și testele sunt consemnate în checklist. Recuperarea parolei, verificarea emailului și ștergerea completă de cont nu sunt încă funcții curente.

## Pregătirea pentru examene

Versiunea curentă salvează un obiectiv de examen și permite exersarea materiei încărcate. Identificarea programei oficiale și importul manualelor prin API nu sunt implementate. Înaintea lor alegem examenele, clasele și materiile prioritare, verificăm sursele oficiale și drepturile asupra conținutului. Programa afișată va trebui să indice sursa, anul și versiunea; o asociere estimată de AI nu se poate prezenta ca mapare oficială.

## Audio export și extinderi

Audio completează studiul și se generează la cererea proprietarului, în RO/EN și în limba sursei. Ionuț lucrează la îmbunătățirea audio/video, separat de această rundă. Un pipeline premium și modul cinematic interactiv necesită integrare și teste înainte de a fi prezentate ca active.

PDF-ul local cu diacritice este disponibil pentru sursă, lecții, carduri, quiz și pachet complet. ILOVEAPI este o opțiune de conversie explorată de coleg, nu o dependență a exportului actual. Markdown și Anki rămân exporturi disponibile prin API.

Serverul AI propriu gratuit, cheile personale ale furnizorilor, camerele cu profesor personalizat/antrenare și biblioteca de nișă cu plată sunt extensii pentru pitch. Necesită infrastructură, licențe, evaluare și finanțare. Nu există prețuri, reduceri sau plăți active.

## Demo și prezentare

Demo-ul trebuie să arate un material permis pentru utilizare, alegerea conceptelor, o lecție, un răspuns cu citat și un quiz. Verificăm separat refuzul unei întrebări absente și izolarea materialului privat. Nu există încă rezultate măsurate privind eficiența învățării; un pilot trebuie să măsoare timpul până la recapitulare și înțelegerea materiei.

Găzduirea se mută integral pe Render, într-un singur Web Service Docker: Next.js pe portul public și FastAPI pe loopback în același container, cu cereri pe aceeași origine. Echipa a ales Render Free pentru demo: SQLite, documentele și media sunt temporare sub `/var/data` și se pot pierde la restart, redeploy sau oprirea automată. Serviciul se oprește după 15 minute fără trafic și repornește la acces, în aproximativ un minut. Migrarea nu este declarată live până la verificarea URL-ului și autentificării. Testarea redeployului va confirma resetarea așteptată, fără promisiune de persistență.

Demo-ul Vercel anterior depindea de un API pe PC și a produs erori 502 după sleep; nu mai este adresa oficială. Cheia Gemini rămâne secret de backend și nu se introduce în frontend, documente sau prezentare. Pașii curenți sunt în [deployment_demo.md](deployment_demo.md).

Templateul PowerPoint a fost inspectat, fără modificare. Structura sa și cronometrarea sunt în [prezentare_template.md](prezentare_template.md). Prezentarea Canva se realizează ulterior, cu maximum zece pagini totale la depunere, păstrând declararea bazei preexistente Book2Sound/Book2Course și clarificarea eligibilității cu organizatorii.

## Decizii deschise

- Examenul, materia și nivelul prioritare pentru pilot.
- Sursele oficiale și licențele pentru programe/manuale.
- Rezultatele măsurate cu utilizatori și ce responsabilitate are fiecare membru.
- Protecția datelor și procedurile pentru conturi folosite de minori.
- Găzduirea persistentă și costul real al serviciilor AI înaintea unui abonament.
