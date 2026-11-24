# Lezioni → bozze per X

Ogni ora (GitHub Actions) legge la sitemap del sito. Per ogni lezione nuova scarica la GIF di anteprima, la converte in MP4
e apre una *issue* con il testo del post pronto da copiare in Buffer. Il video sta in `video/`. Non pubblica niente da solo.

## Per attivarlo
1. Compila `config.json`: `sitemap_url`, `filtro_lezioni` (un pezzo comune degli indirizzi delle lezioni, es. `/lezione/`), `hashtag`.
2. Prova in locale: `python3 lezioni_x.py --prova` (serve `ffmpeg`).
3. Crea un repository **privato** su GitHub e caricaci questa cartella.
4. In GitHub: Settings → Actions → General → Workflow permissions → «Read and write permissions».
5. Scheda Actions → «Nuove lezioni → bozze per X» → Run workflow. Il primo giro segna le lezioni esistenti come già viste.

## Se il sito risponde «403 Forbidden»
Il sito rifiuta le richieste automatiche. Lo script si presenta come `lezioni-x/1.0` e non finge di essere un browser.
Chi gestisce il sito (o la sua protezione, per esempio Cloudflare) deve consentire quel nome sulla sitemap e sulle pagine `/en/store/videos/v/…`.
Se preferisce una chiave: la si imposta come segreto `LEZIONI_X_CHIAVE` (e in locale come variabile d'ambiente) e viaggia nell'intestazione `X-Lezioni-Chiave`.
Per cambiare il nome: variabile `LEZIONI_X_AGENTE`.
