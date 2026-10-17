# Lansarea 4Next pe Render

## Decizia actuală și starea verificării

Echipa a abandonat demo-ul Vercel care trimitea cererile către un backend de pe PC: după sleep, colegii au primit 502. Noua țintă găzduiește interfața și API-ul împreună pe **Render Free**, fără dependență de PC sau tunel. Utilizatorul s-a autentificat în Render și a ales explicit varianta gratuită, acceptând resetarea datelor. Nu activăm un plan cu plată.

**Deploymentul Render și URL-ul final sunt încă în verificare.** Nu prezentăm o adresă anticipată ca fiind funcțională. Sursa pregătită pentru migrare are 78/78 teste backend, 90% acoperire pentru codul activ, 4/4 teste proxy frontend, plus lint, TypeScript și build. Verificările noi se adaugă după execuție.

## Un serviciu pentru interfață și API

Sursele pregătite sunt `render.yaml`, `Dockerfile.render` și `scripts/run_render.py`. Blueprintul definește `4next-study`, Docker Free în Frankfurt, branch `main`, fără disc și fără publicare automată (`autoDeployTrigger: off`). Web Service-ul Docker pornește două procese în același container:

- Next.js ascultă pe `0.0.0.0:$PORT`, portul public atribuit de Render.
- FastAPI ascultă exclusiv pe `127.0.0.1:8000`, accesibil doar din container.
- Proxyul Next.js trimite `/api` și `/media` către API-ul intern. Browserul folosește aceeași origine pentru pagină, cookie și cereri.
- Supervisorul oprește containerul dacă unul dintre procese cade și trimite oprirea ambelor procese. Endpointul `/api/health` verifică API-ul și o cerere SQLite limitată, fără apeluri către Gemini.

Astfel, oprirea calculatorului echipei nu mai oprește aplicația găzduită. Nu se folosesc `localhost:8000` în codul trimis browserului, Cloudflare Quick Tunnel sau vechiul gateway demo pentru această lansare.

## Datele din demo sunt temporare

SQLite, uploadurile și media se configurează sub `/var/data`, **fără disc montat** pe Free. Conturile, sesiunile, documentele și progresul se pot pierde la restart, redeploy sau oprirea automată a serviciului. Directorul `/var/data` singur nu asigură persistența.

Render Free oprește serviciul după 15 minute fără trafic; primul acces ulterior îl reactivează în aproximativ un minut. Aceste limite sunt descrise în [documentația Render Free](https://render.com/docs/free). Aplicația trebuie să afișeze un mesaj clar despre datele temporare. Contul demo se înregistrează manual și poate necesita recreare după resetare; nu există parolă implicită sau cheie de test publicată în Git.

Pentru păstrarea datelor ulterior, putem atașa un disc unui serviciu cu plată sau migra datele și fișierele în servicii externe. Această etapă necesită buget aprobat și verificarea backupului. Nu face parte din lansarea gratuită aleasă. [Render Persistent Disks](https://render.com/docs/disks)

## Configurația de mediu

| Variabilă | Unde și de ce |
| --- | --- |
| `PORT` | Este furnizat de Render; Next.js ascultă public pe acest port. Nu este portul API-ului intern. |
| `BACKEND_ORIGIN` | Supervisorul o setează numai pentru serverul Next.js la `http://127.0.0.1:8000`. Nu se configurează către PC. |
| `NEXT_PUBLIC_API_URL` | Gol în Dockerfile la build: browserul cere `/api` și `/media` pe aceeași origine. Nu conține secrete. |
| `NEXT_PUBLIC_STORAGE_MODE` | Build argument implicit `ephemeral`; afișează mesajul despre datele temporare. Nu reprezintă un secret. |
| `DATA_DIR` | `/var/data`, rădăcina temporară pentru uploaduri și media în demo-ul Free. |
| `STORAGE_MODE` | `ephemeral`, descrie modul de stocare al demo-ului; nu activează persistență. |
| `DATABASE_PATH` | `/var/data/book2course.db`, baza temporară de conturi și cursuri. |
| `COOKIE_SECURE` | Supervisorul impune `true` pentru backend. Cookie-ul rămâne HttpOnly și SameSite=Lax. |
| `RENDER_EXTERNAL_URL` | Furnizată de Render; supervisorul o validează ca origine HTTPS și o adaugă în originile permise. |
| `ALLOWED_ORIGINS` | Opțional pentru alte origini HTTPS explicite. Supervisorul adaugă URL-ul real Render; fără `*` sau cale. |
| `GEMINI_API_KEY` | Secret introdus în Render Environment. Niciodată prefix `NEXT_PUBLIC_`, Git, Dockerfile sau document de proiect. |
| `GEMINI_MODEL` | Modelul ales pentru apelurile backend; lipsa/disponibilitatea furnizorului este tratată prin fallback extractiv etichetat. |
| `PDF_FONT_PATH` | Opțional dacă fontul Unicode nu este găsit automat; imaginea trebuie să includă un font compatibil cu diacriticele. |
| `NEXT_PUBLIC_UPLOAD_LIMIT_MB` | Build argument implicit `15` în Dockerfile; limita interfeței se aliniază cu backendul. |

`backend/.env` este doar configurație locală ignorată. În cloud, variabilele se setează în Render; nu încărcăm fișierul local. Mediul procesului are prioritate pentru backend. Modificarea unei variabile `NEXT_PUBLIC_*` necesită rebuild, deoarece se include în JavaScriptul trimis browserului. O cheie Gemini schimbată în mediul serverului necesită repornire/redeploy și reverificare.

Supervisorul transmite procesului Node doar o listă restrânsă de variabile; cheia Gemini și secretele backendului nu sunt moștenite de frontend. `.dockerignore` exclude SQLite, sesiunile, documentele personale, parolele, `.env`, `.venv`, `node_modules` și directoarele media locale din contextul imaginii. Dacă un cont există pe vechiul demo, aceasta nu înseamnă că există și pe Render.

## Pași concreți în Render Dashboard

1. Deschide Dashboard în contul autentificat și verifică workspace-ul echipei.
2. Alege **New → Web Service**, conectează repository-ul GitHub `archimex2026/4next` și acordă acces numai repository-ului necesar. Selectează branch-ul integrat și verificat; nu presupune că merge-ul a avut deja loc.
3. Alege runtime **Docker**, context `.` din rădăcina repository-ului și Dockerfile Path `./Dockerfile.render`. Nu folosi separat Dockerfile-ul vechi al frontendului sau backendului pentru acest serviciu complet.
4. Selectează planul **Free**. Nu adăuga disc și nu activa opțiuni cu cost. Denumirea serviciului determină URL-ul disponibil; nu promite un nume înaintea confirmării Render.
5. Configurează variabilele serverului și secretul Gemini. Păstrează browserul pe aceeași origine și API-ul pe loopback. Nu dezvălui valoarea cheii în capturi sau loguri.
6. Setează Health Check Path `/api/health` și creează serviciul. Citește logurile buildului; existența unui serviciu în listă nu confirmă deployment reușit.
7. După starea **Live**, verifică URL-ul HTTPS, apoi urmează lista de acceptare de mai jos. Blueprintul are `autoDeployTrigger: off`; după un push verificat, folosește **Manual Deploy → Deploy latest commit**. Publicarea automată se poate activa ulterior numai după conectarea integrării GitHub; URL-ul public al repository-ului singur nu acordă aceste drepturi.
Dacă se folosește **New → Blueprint**, selectează repository-ul după integrarea sursei verificate pe `main`, verifică preview-ul `render.yaml` și confirmă că apare numai serviciul Free fără disc. Nu dubla serviciul dacă a fost deja creat din Web Service.

8. Completează în README și în documentele de proiect URL-ul real, rezultatele verificărilor și limitele Free. Prezentarea Canva se pregătește după stabilizarea demo-ului.

Dacă accesul GitHub sau Render necesită autentificare umană, pregătirea codului, testele și commitul pot continua. Lipsa accesului la serviciul extern nu blochează integrarea sursei verificate. Singurele confirmări necesare la configurare sunt accesul contului și orice schimbare care ar activa facturarea; Free a fost deja ales explicit.

## Verificări ale configurației pregătite

- Sursa locală a trecut 78/78 teste backend, 90% acoperire cod activ, 4/4 teste proxy, lint, TypeScript și build de producție.
- `render.yaml` a trecut validarea locală cu schema oficială Draft 2020-12. CLI Render 2.29 este instalat, însă autentificarea browserului nu autentifică automat CLI-ul; validarea autentificată de platformă se verifică în preview-ul Dashboard după push.
- GitHub Actions include acum buildul Docker și un smoke test real al containerului prin `scripts/smoke_render.py` pentru health, catalog și PDF. La această actualizare, noul job CI este în așteptarea pushului, iar Docker nu este instalat local. Nu declarăm încă imaginea construită sau serviciul Render live.

## Checklist înainte de distribuirea linkului

- [ ] Buildul Docker reușește, ambele procese pornesc, health checkul răspunde.
- [ ] Pagina principală și API-ul răspund pe HTTPS; nu apar secrete sau erori de proxy în răspuns.
- [ ] Un cont nou se înregistrează, se autentifică și se poate deloga; cookie-ul are Secure și HttpOnly.
- [ ] Un material privat nu poate fi citit/exportat din alt cont sau ca vizitator.
- [ ] Inspecție și upload PDF real, RO/EN, cu selectare concept și generare în limba documentului.
- [ ] Lecții, highlights, notițe, progres, flashcard și quiz funcționează.
- [ ] Chatul oferă citat exact pentru o întrebare prezentă și refuz pentru una absentă, inclusiv PDF cu rânduri vizuale rupte.
- [ ] Cele cinci exporturi PDF sunt lizibile și includ diacritice; Markdown/Anki rămân disponibile.
- [ ] Publicare/retragere, rating, clasă, invitație și revocarea partajării funcționează.
- [ ] Coșul oprește accesul, restaurarea este privată și ștergerea definitivă reușește.
- [ ] Funcțiile se verifică fără API-ul/tunelul calculatorului echipei.
- [ ] Mesajul despre date temporare este vizibil; resetarea după restart/redeploy este acceptată și documentată.
- [ ] Linkul final și baza de teste actuală sunt consemnate; nu declarăm automat funcțiile viitoare drept disponibile.

## Istoricul Vercel și diagnosticul 502

Pe 17 octombrie 2026, configurația anterioară a trecut verificări pentru homepage/API, autentificare HTTPS, upload și export PDF, chat/citate/refuz, clase și coș. Interfața era la `4next-study.vercel.app`, cu backend izolat pe PC la portul 18000, gateway secret și tunel. `4next.vercel.app` era ocupat.

Ulterior, echipa a raportat 502 după sleep. Interfața putea fi disponibilă în timp ce backendul nu mai răspundea. Acesta este motivul migrării integrale pe Render. URL-ul Vercel și rezultatele sale rămân istoric; nu sunt o promisiune de disponibilitate curentă și nu se distribuie ca adresă oficială a noii lansări.

Cheia Gemini a răspuns unui apel JSON real și unui upload în mod `ai_grounded` în runda anterioară. Alte cereri au întâlnit indisponibilitatea furnizorului și au folosit fallbackul extractiv. Disponibilitatea modelului rămâne distinctă de starea serverului Render.

Surse tehnice: [Render Web Services](https://render.com/docs/web-services), [Render Free](https://render.com/docs/free), [Render Persistent Disks](https://render.com/docs/disks).
