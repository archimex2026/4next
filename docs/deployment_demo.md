# Lansarea demo 4Next

## Configurația aleasă

Interfața Next.js se publică pe Vercel, în proiectul `4next` din echipa `mflaviusgabriel`. `4next.vercel.app` aparține altui proiect; alternativa rezervată și verificată este `4next-study.vercel.app`.

API-ul FastAPI rulează pe acest PC, pe `127.0.0.1:18000`, prin `app.demo_gateway:create_demo_app --factory`. Un Cloudflare Quick Tunnel temporar îl conectează la Vercel. Instanța demo folosește exclusiv `.local-demo/data`: SQLite, uploaduri și media separate. Nu copiază conturile, sesiunile sau documentele din instanța de dezvoltare de pe portul 8000. Sunt adăugate două exemple educaționale publice originale.

Gateway-ul verifică o cheie aleatoare de server înainte să citească cererea sau să apeleze API-ul. Accesul direct la tunel fără cheie primește 404, inclusiv pentru catalog, documentație și media. Verificarea căilor rezolvate și a legăturilor către baza locală previne reutilizarea accidentală a stocării de dezvoltare.

Proxy-ul Next.js trimite cheia exclusiv în cererea către backend și înlocuiește orice valoare furnizată de client. Browserul folosește `/api` și `/media` pe aceeași origine cu site-ul. Cookie-ul de sesiune rămâne HttpOnly, Secure și SameSite=Lax. Originea publică este permisă explicit în backend; mutațiile cross-site rămân respinse. Nu activa loguri `DEBUG=next:*` care ar putea include antete interne.

## Variabile de mediu

| Loc | Variabilă | Rol |
| --- | --- | --- |
| Vercel Production | `NEXT_PUBLIC_API_URL` gol | Cereri din browser pe aceeași origine. Nu conține secrete. |
| Vercel Production | `BACKEND_ORIGIN` | Adresa HTTPS a tunelului curent; numai originea, fără cale. |
| Vercel Production Secret | `DEMO_PROXY_TOKEN` | Cheia de acces server către gateway. Niciodată prefix `NEXT_PUBLIC_`. |
| Frontend opțional | `NEXT_PUBLIC_UPLOAD_LIMIT_MB` | Implicit 4 MB în producție pentru compatibilitate cu proxy-ul; local 15 MB. |
| Backend | `GEMINI_API_KEY`, `GEMINI_MODEL` | Citite din mediul procesului sau din fișierul local ignorat `backend/.env`. Cheia nu este trimisă către Vercel/frontend. |
| Backend demo | `DATA_DIR`, `DATABASE_PATH` | Setate explicit de script în `.local-demo/data`. |
| Backend demo | `DEMO_PROXY_TOKEN_FILE` | Fișierul local ignorat `.local-demo/proxy-token.txt`; aceeași cheie ca în Vercel. |
| Backend demo | `COOKIE_SECURE`, `ALLOWED_ORIGINS` | HTTPS și originea exactă a site-ului; setate de script. |

Fișierele `.env.example` sunt șabloane fără secrete. Variabilele procesului au prioritate în backend; schimbarea cheii presupune repornirea backendului. Variabilele `NEXT_PUBLIC_*` se includ în buildul frontend și necesită rebuild. Cheia Gemini existentă a răspuns unui apel JSON real; fluxul de upload a produs și un curs în modul `ai_grounded`. Dacă furnizorul eșuează, extragerea locală rămâne etichetată explicit.

## Pornire și repornire

Din rădăcina repo-ului, după instalarea dependențelor:

```powershell
.\scripts\start-demo-backend.ps1
```

În alt terminal, clientul oficial descărcat pentru demo:

```powershell
H:\4Next\tools\cloudflared.exe tunnel --no-autoupdate --url http://127.0.0.1:18000 --protocol http2
```

La pornirea unui Quick Tunnel nou, adresa se poate schimba. Actualizează `BACKEND_ORIGIN` în setările proiectului Vercel și publică din nou buildul. Nu expune portul local 8000 și nu porni un tunel fără gateway-ul cu cheie. Scriptul refuză pornirea dacă lipsește fișierul cheii; nu există parolă implicită în cod. La rotirea cheii trebuie actualizat atât fișierul local, cât și secretul Vercel, apoi repornire/redeployment.

Procesele pornite pentru sesiunea curentă rulează cu ferestre ascunse, cu loguri în `.local-demo`. Oprește numai procesele demo identificate după port și linia de comandă. Instanța locală 8000 și proiectul vechi 8001 rămân independente. Datele demo persistă pe disc între reporniri, dar nu sunt găzduite în cloud și nu intră în Git.

## Publicare și limite

Integrarea GitHub a contului Vercel nu are încă acces la repo. Pentru această lansare pot fi încărcate direct sursele frontend verificate, fără `.env`, baze de date, chei, `node_modules` sau artefacte de build. Publicarea automată la push necesită conectarea ulterioară a repo-ului în Vercel; un push GitHub singur nu actualizează site-ul în această configurație.

Demo-ul depinde de PC pornit, procesul backend, tunel și internet. Quick Tunnel nu oferă o promisiune de disponibilitate permanentă. Înaintea folosirii cu date reale, mutăm același backend pe o instanță cu volum persistent și backup pentru SQLite/uploaduri/media, păstrăm proxy-ul HTTPS și actualizăm originea. Nu punem SQLite într-un filesystem serverless temporar.

Coșul expiră logic după cinci zile; eliminarea fizică se face la următoarea pornire/solicitare API. Fișierele blocate sunt reîncercate dintr-o coadă SQLite. Nu există încă un job programat independent de traficul aplicației. Recuperarea parolei, verificarea emailului, istoricul persistent de chat, FTS5 și audio premium sunt diferențe documentate în auditul de backend.

Surse tehnice: [Vercel routing](https://vercel.com/docs/routing), [Vercel environment variables](https://vercel.com/docs/environment-variables), [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
