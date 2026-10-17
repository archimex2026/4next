# 4Next

4Next este un spațiu de studiu care transformă materialele proprii ale elevilor și studenților în cursuri scurte, lecții, flashcarduri și quizuri. Direcția produsului este să susțină înțelegerea și pregătirea pentru examene, păstrând materialul sursă în centrul experienței.

Aplicația este în lucru. Funcțiile descrise mai jos reflectă starea actuală a codului; chatul bazat pe PDF, maparea la programe școlare și personalizarea prin cont nu sunt încă implementate.

## Ce poți face acum

- Încarcă un PDF, EPUB, DOCX, TXT sau Markdown ori lipește text.
- Generează un curs structurat în lecții, cu explicații, idei-cheie, exemple, acțiuni și diagrame Mermaid.
- Studiază cu flashcarduri și quizuri cu punctaj și explicații.
- Urmărește progresul lecțiilor și adaugă notițe personale.
- Ascultă lecții audio în română sau engleză; generarea fișierelor audio și video continuă în fundal.
- Deschide lecții video și descarcă materiale precum ghiduri Markdown, audio, video și diagrame.
- Explorează o bibliotecă de cursuri cu date demo, disponibilă și ca rezervă când backendul nu răspunde.

Generatorul curent folosește extragerea textului și reguli euristice pentru a organiza materialul. Codul conține și un analizor Gemini, însă fluxul de încărcare nu îl folosește în prezent. Limba documentului nu este detectată și impusă pentru toate materialele generate; alegerea română/engleză din formular privește limba audio. Calitatea extragerii depinde de document, iar PDF-urile scanate pot necesita OCR, care nu este inclus acum.

## Direcția următoare

- Materialele generate să respecte limba documentului și să explice răbdător, ca un profesor.
- Un chat legat de document să răspundă din PDF, să indice pagini sau fragmente și să recunoască atunci când sursa nu conține răspunsul.
- Pregătirea pentru examene să poată lega materialele de programa potrivită, folosind surse oficiale și identificabile.
- Conturile și întrebările de personalizare sunt o etapă ulterioară.

Cerințele și întrebările deschise sunt păstrate în [direcția de produs](docs/directie_produs_4next.md). Direcția vizuală este descrisă în [DESIGN.md](DESIGN.md). Documentul de lucru pentru regulament și prezentare se află în [docs/](docs/).

## Tehnologii

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS 4.
- Backend: FastAPI, Python, SQLite.
- Materiale: PyPDF2, python-docx, parser EPUB propriu, Mermaid, gTTS/edge-tts și FFmpeg prin imageio-ffmpeg.
- Gemini este prezent în codul analizorului, dar nu este conectat la fluxul activ de încărcare.

## Pornire locală

Ai nevoie de Python 3.10+ și Node.js 20.9+.

Pornește API-ul într-un terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Pornește interfața într-un al doilea terminal:

```powershell
cd frontend
npm install
npm run dev
```

Deschide aplicația la [http://localhost:3000](http://localhost:3000). Documentația interactivă a API-ului este la [http://localhost:8000/docs](http://localhost:8000/docs).

Dacă backendul rulează pe altă adresă, setează `NEXT_PUBLIC_API_URL` pentru frontend înainte de pornire. Baza SQLite, fișierele încărcate și media generată sunt locale în `backend/`; configurația actuală nu oferă stocare persistentă pentru o lansare publică.

## Verificări

Testele API se pot rula din rădăcina repository-ului:

```powershell
python -m unittest backend/tests/test_api.py
```

Verificările frontendului:

```powershell
cd frontend
npm run lint
npm run build
```

## Starea lansării

Proiectul este pregătit pentru rulare locală. O lansare publică necesită configurarea backendului, a unei baze de date și a stocării persistente pentru fișiere și media, precum și setarea adreselor API/CORS pentru mediul de producție. Nu există încă un flux complet de deployment Vercel în repository.
