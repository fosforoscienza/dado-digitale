
> Apri questa pagina in [https://fosforoscienza.github.io/dado-digitale/](https://fosforoscienza.github.io/dado-digitale/)

## Usa come Estensione

Questa repository può essere aggiunta come una **estensione** in MakeCode.

* apri [https://makecode.microbit.org/](https://makecode.microbit.org/)
* clicca su **Nuovo Progetto**
* fai clic su **Estensioni** nel menu della ruota dentata
* cerca **https://github.com/fosforoscienza/dado-digitale** ed importa

## Modifica questo progetto

Per modificare questa repository in MakeCode.

* apri [https://makecode.microbit.org/](https://makecode.microbit.org/)
* clicca su **Importa** quindi fai clic su **Importa INDIRIZZO**
* incolla **https://github.com/fosforoscienza/dado-digitale** e clicca importa

#### Metadati (usati per la ricerca, il rendering)

* for PXT/microbit
<script src="https://makecode.com/gh-pages-embed.js"></script><script>makeCodeRender("{{ site.makecode.home_url }}", "{{ site.github.owner_name }}/{{ site.github.repository_name }}");</script>

## Generare un carosello Instagram automatico da testo

Se vuoi trasformare un testo in slide 4:5 (1080x1350), puoi usare lo script locale:

1. Crea un file di testo, ad esempio `contenuto.txt`.
2. Esegui:

```bash
node scripts-genera-carosello.js --input contenuto.txt --output dist/carousel --title "Titolo carosello"
```

Lo script:
- divide automaticamente il testo in blocchi leggibili,
- genera una slide HTML per ogni blocco,
- crea `index.html` per anteprima rapida.

Output finale: file in `dist/carousel/slide-XX.html` pronti da esportare come immagini per Instagram.
