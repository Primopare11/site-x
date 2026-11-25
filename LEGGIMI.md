# Lezioni → bozze per X

Ogni 3 ore (GitHub Actions) legge il feed JSON del sito (`feed_url` in `config.json`; in mancanza, la sitemap). Per ogni lezione nuova scarica la GIF di anteprima, la converte in MP4
e manda a Buffer il post (testo + video) come bozza, da approvare a mano. Il video sta in `video/`.
Per far pubblicare i post da soli nel prossimo slot libero, metti `"saveToDraft": False` in `manda_a_buffer()` (`lezioni_x.py`).

## Per attivarlo
1. Compila `config.json`: `sitemap_url`, `filtro_lezioni` (un pezzo comune degli indirizzi delle lezioni, es. `/lezione/`), `hashtag`.
2. Prova in locale: `python3 lezioni_x.py --prova` (serve `ffmpeg`).
3. Crea un repository **privato** su GitHub e caricaci questa cartella.
4. Imposta il segreto `BUFFER_TOKEN` e la variabile `BUFFER_CHANNEL_ID` (più `VIDEO_URL_BASE`, l'indirizzo pubblico di `video/`).
5. In GitHub: Settings → Actions → General → Workflow permissions → «Read and write permissions».
6. Scheda Actions → «Nuove lezioni → bozze per X» → Run workflow. Il primo giro segna le lezioni esistenti come già viste.

## Se il sito risponde «403 Forbidden»
Il sito rifiuta le richieste automatiche. Lo script si presenta come `lezioni-x/1.0` e non finge di essere un browser.
Chi gestisce il sito (o la sua protezione, per esempio Cloudflare) deve consentire quel nome sulla sitemap e sulle pagine `/en/store/videos/v/…`.
Se preferisce una chiave: la si imposta come segreto `LEZIONI_X_CHIAVE` (e in locale come variabile d'ambiente) e viaggia nell'intestazione `X-Lezioni-Chiave`.
Per cambiare il nome: variabile `LEZIONI_X_AGENTE`.
