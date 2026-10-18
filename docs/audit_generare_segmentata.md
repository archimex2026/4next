# Audit și remediere pentru documentele mari

18 octombrie 2026. Au fost inspectate README, DESIGN, toate documentele din `docs`, instrucțiunile din `for_AI_Agents`, capturile `miscellaneous/ai-fail-2`, codul activ, CI GitHub și serviciul Render. Documentul Word a fost corectat punctual și toate cele șase pagini au fost inspectate după export local prin Word. Capturile originale rămân dovezi istorice.

## Probleme confirmate înainte de modificări

| Prioritate | Observație | Cauză / acțiune |
| --- | --- | --- |
| P1 | 127 pagini / 120 minute, cu numai trei lecții în capturi | Un singur apel global, plafon de 12 lecții și numai 4–8 carduri / 3–6 quizuri. Nu exista stare pe segmente. |
| P1 | Citări valide cu explicații semantic greșite | Verificatorul putea aproba generalizările unei surse simplificate. S-a reprodus inclusiv după primul patch; nu a fost considerat acceptabil doar pentru că JSON-ul era valid. |
| P1 | Codul și comentariile din două coloane se intercalau | Extragerea ordona geometric rândurile. Pagina 79 a fost verificată; acum se urmărește ordinea obiectelor text PDF. |
| P2 | Fragmente tăiate la `vs.` și text de slide amestecat | Slide-urile scurte sunt păstrate ca unități complete de dovezi. Extragerea nu poate reconstrui perfect orice diagramă sau PDF arbitrar. |
| P2 | O întrebare opțională invalidă elimina lecțiile valide | Validarea structurală a cardurilor/quizurilor se face separat. Practica ambiguă poate fi omisă de verificator. |
| P2 | Documentele spuneau simultan Live și „în build” | README, handoff, checklisturi și DOCX disting versiunea publică de schimbările locale. |

PDF-ul real are 127 pagini și aproximativ 32.000 caractere de text extras: cazul încape în vechiul context de 75.000 caractere. Depășirea contextului nu este cauza confirmată pentru acest fișier. Se păstrează în afara Git PDF-ul și rezultatele private de evaluare.

## Implementare

Documentele de peste 24 pagini/secțiuni sau 75.000 caractere primesc un plan consecutiv, cu maximum 12 pagini și 12.000 caractere pe segment. Paginile foarte lungi sunt împărțite prin intervale de caractere; fiecare caracter și paginile goale intră exact o dată în plan. Nu se inventează capitole pe baza numerelor de pagină.

Uploadul creează prima parte. Proprietarul continuă secvențial din spațiul de studiu și poate opri după partea curentă. Tabela SQLite aditivă `generation_segments` păstrează planul. Un segment și materialele lui se salvează în aceeași tranzacție; un eșec la salvare se reia fără rezultat pe jumătate. Indexul trimis de client face repetarea unei cereri idempotentă. Notițele, identificatorii și progresul existent sunt păstrate. Deduplicarea elimină explicații și întrebări identice după normalizarea spațiilor/literelor; deduplicarea semantică perfectă nu este promisă.

Durata selectată se distribuie între segmente și influențează numărul solicitat de lecții. Profunzimea schimbă instrucțiunile explicațiilor. Pentru un document mare și o sesiune foarte scurtă, procesarea tuturor părților nu implică învățarea lor în durata aleasă. UI-ul raportează separat segmente salvate, pagini procesate și pagini citate în lecții; niciunul nu este o măsurătoare a înțelegerii elevului.

Verificarea cere separat `supported` și `semantically_valid`. Sunt respinse generalizările false, confuzia atribuire/redeclarare/inițializare și quizurile fără un răspuns unic. Când există timp, un răspuns respins este corectat o singură dată folosind feedbackul verificatorului. Întregul ciclu AI este limitat la 105 secunde, sub timeoutul proxy de 120 secunde; la indisponibilitate sau respingere rămân extrase etichetate. Nu se schimbă cheia sau modelele configurate.

## Verificări

- Baza inițială: 89 teste backend trecute. Regresiile noi verifică planul complet de 127 pagini, caracterele/paginile goale, rollback, reluare, acces, coș în timpul generării, păstrarea notițelor, citări și verdictul semantic.
- Verificare semantică reală stratificată pe paginile 37–48, 73–84 și 109–120: nouă lecții AI validate. În segmentul despre variabile, prima propunere a fost respinsă pentru afirmații prea generale și confuzia inițializare/atribuire; varianta corectată a trecut verificarea și inspecția manuală. Aceasta nu reprezintă evaluare pedagogică exhaustivă.
- Interfață verificată în browser la 390 px: progres accesibil, plan pe pagini, continuare după un răspuns pierdut și finalizare fără dublare; fără erori în consola browserului. Lint, TypeScript, build și cele cinci teste proxy trec.
- Validare finală: **104/104 teste backend, 91% acoperire pentru codul activ**, lint, TypeScript, build de producție și **5/5 teste proxy** trecute.
- Rularea API reală pe PDF-ul de 127 pagini / 120 minute a încheiat **11/11 segmente**, cu **31 lecții/materiale de lectură, 44 carduri și 49 quizuri**. Dintre lecții, **14 sunt explicații AI validate și 17 sunt extrase etichetate**. Citările lecțiilor ajung pe **81 pagini**, distinct de cele 127 procesate. Au existat erori de furnizor 429/503/504; acestea nu sunt prezentate drept rezultate AI. Exportul PDF complet a reușit (183.842 octeți).
- Rularea anterioară a primului patch a produs 32 materiale, dar controlul semantic a găsit încă generalizări greșite. Acest rezultat a declanșat întărirea verdictului și corectarea limitată; nu este rezultatul final acceptat.
- Artefactele QA private sunt în `H:\4Next\artifact-qa\large-pdf`, în afara repository-ului. Testele CI folosesc numai fixture-uri originale/sintetice. Ultima ajustare de cotă împiedică o nouă generare când verificatorul este indisponibil; a trecut suita de 104 teste.

## Render și publicare

Conectorul Render funcționează după reconectarea OAuth. Workspace confirmat: `4next`, `tea-db9t6kqjnfac73di4ung`; serviciu: `srv-db9ti25g1s2s73a053kg`, Frankfurt Free, Docker, branch `main`, deploy automat dezactivat. Versiunea Live inspectată este `b2579fc8992863a09bdb6c73187ed8fa92729876`. Homepage-ul, `/api/health` și catalogul public răspund 200. Logurile conțin erori istorice ale furnizorului și respingeri de conținut; niciun secret nu a fost solicitat sau publicat.

Această verificare nu publică automat codul local. Un redeploy al serviciului Free poate reseta conturile, documentele și progresul. Modificările se integrează și se publică numai după verificările sursei; nu se activează planuri sau discuri cu plată. La rollback se poate reveni la imaginea anterioară; migrarea adaugă numai o tabelă, pe care codul anterior o ignoră. Datele salvate exclusiv pe Free nu au garanție de recuperare după restart.

## Lucrări care rămân separate

Evaluare cu profesori/elevi și alte surse, persistență/backup, istoric chat, recuperare parolă, moderare, mai multe documente și audio/video premium. Acestea nu au fost implementate prin acest audit. Codul legacy de video/diagrame a fost identificat ca simplificare posibilă prin Ponytail, dar ștergerea lui nu repară incidentul și ar afecta lucrul separat al echipei.

## Rezultatul Ponytail pentru codul moștenit

delete: `backend/app/services/video_generator.py` (488 linii), fără apelanți în codul activ; posibil de eliminat numai după coordonarea cu Ionuț.

delete: `backend/app/services/diagram_generator.py` (41 linii), fără apelanți în codul activ; aceeași coordonare înaintea ștergerii.

net: -529 lines, -0 deps possible. Aceste ștergeri nu au fost aplicate în reparație.
